import numpy
import geopandas
import sys
import pyproj

from ._coordinate_system import _create_transform_crs


def _geojson_to_raster(path_to_geojson, x_dim, y_dim, grid_mapping_variable):
    
    def fill_shape(column_row, counter, list_of_cells):
        geojson_array[column_row[0], column_row[1]] = True
        cells_to_check = find_cells_to_check(column_row[0], column_row[1])

        if counter <= 2500:
            for cell in cells_to_check:
                counter += 1
                counter, list_of_cells = fill_shape(cell, counter, list_of_cells)
        else:
            if len(cells_to_check) > 0:
                for cell in cells_to_check:
                    if cell not in list_of_cells:
                        list_of_cells.append(cell)
            
        return counter, list_of_cells

    def find_cells_to_check(column, row):
        list_of_cells = []
        if not geojson_array[column - 1, row]:
            list_of_cells.append((column - 1, row))
        if not geojson_array[column, row - 1]:
            list_of_cells.append((column, row - 1))
        if not geojson_array[column, row + 1]:
            list_of_cells.append((column, row + 1))
        if not geojson_array[column + 1, row]:
            list_of_cells.append((column + 1, row))
        
        return list_of_cells

    def outline_shape(shape):
        coordinate_array = numpy.array(shape.exterior.coords)
        
        dif_in_x = x_dim - numpy.append(x_dim[1:], x_dim[0])
        dif_in_y = y_dim - numpy.append(y_dim[1:], y_dim[0])
        avg_dif_in_x = abs(numpy.mean(dif_in_x[:-1]))
        avg_dif_in_y = abs(numpy.mean(dif_in_y[:-1]))
        
        x_coordinates = numpy.tile(coordinate_array[:, 0], (len(x_dim), 1))
        y_coordinates = numpy.tile(coordinate_array[:, 1], (len(y_dim), 1))
        
        x_dimensions = numpy.tile(x_dim, (len(coordinate_array[:, 0]), 1))
        y_dimensions = numpy.tile(y_dim, (len(coordinate_array[:, 1]), 1))
        
        x_subtract = abs(x_dimensions - x_coordinates.transpose())
        y_subtract = abs(y_dimensions - y_coordinates.transpose())
        
        x_mins = x_subtract.min(axis=1)
        y_mins = y_subtract.min(axis=1)
        
        if min(x_mins) > avg_dif_in_x or min(y_mins) > avg_dif_in_y:
            sys.exit('geojson does not overlap the array')
        else:
            x_min_array = numpy.tile(x_mins, (len(x_dim), 1)).transpose()
            y_min_array = numpy.tile(y_mins, (len(y_dim), 1)).transpose()
            
            x_div_array = numpy.equal(x_subtract, x_min_array)
            y_div_array = numpy.equal(y_subtract, y_min_array)
            
            x_row_number, x_indices = numpy.where(x_div_array == True)
            _, x_rows = numpy.unique(x_row_number, return_index=True)
            x_indices = x_indices[x_rows]
            
            y_row_number, y_indices = numpy.where(y_div_array == True)
            _, y_rows = numpy.unique(y_row_number, return_index=True)
            y_indices = y_indices[y_rows]
            
            all_indices = numpy.column_stack((y_indices, x_indices))
            unique_indices = numpy.unique(all_indices, axis=0, return_index=True)
            unique_indices_with_ordered_column = numpy.column_stack((unique_indices[0], unique_indices[1]))
            ordered_indices = unique_indices_with_ordered_column[unique_indices_with_ordered_column[:, 2].argsort()][:, :2]

            shifted_indecies = numpy.row_stack((ordered_indices[1:, :], ordered_indices[0, :]))
            difference_in_indecies = shifted_indecies - ordered_indices
            
            spots_to_fill = numpy.row_stack((numpy.argwhere(difference_in_indecies > 1), numpy.argwhere(difference_in_indecies < -1)))
            rows_to_fill = numpy.sort(numpy.unique(spots_to_fill[:,0]))[::-1]
            
            for row_index in rows_to_fill:
                first_cell = ordered_indices[row_index]
                change_in_y = difference_in_indecies[row_index, 0]
                change_in_x = difference_in_indecies[row_index, 1]
                
                array_shape = (max(abs(change_in_y) - 1, abs(change_in_x) - 1), 2)
                new_array = numpy.full(array_shape, 0, dtype=int)
                
                if change_in_y != 0:
                    y_direction = change_in_y / abs(change_in_y)
                else:
                    y_direction = 0
                
                if change_in_x != 0:
                    x_direction = change_in_x / abs(change_in_x)
                else:
                    x_direction = 0
                
                for index, row in enumerate(new_array[:]):
                    if index >= abs(change_in_y):
                        if index == 0:
                            row[0] = first_cell[0]
                        else:
                            row[0] = new_array[index - 1, 0]
                    else:
                        row[0] = first_cell[0] + (index + 1) * y_direction
                
                    if index >= abs(change_in_x):
                        if index == 0:
                            row[1] = first_cell[1]
                        else:
                            row[1] = new_array[index - 1, 1]
                    else:
                        row[1] = first_cell[1] + (index + 1) * x_direction
                        
                ordered_indices = numpy.insert(ordered_indices, row_index + 1, new_array, axis=0)
            
            list_of_indices = len(x_dim) * ordered_indices[:,0] + ordered_indices[:,1]
            numpy.put(geojson_array, list_of_indices, True)
    
            centroid = shape.centroid.coords[0]
            y_centroid_subtrace = abs(y_dim - centroid[1])
            y_centroid_min = y_centroid_subtrace.min()
            y_centroid_index = numpy.where(y_centroid_subtrace == y_centroid_min)[0][0]
            
            x_centroid_subtrace = abs(x_dim - centroid[0])
            x_centroid_min = x_centroid_subtrace.min()
            x_centroid_index = numpy.where(x_centroid_subtrace == x_centroid_min)[0][0]
    
            column_row = (y_centroid_index, x_centroid_index)
            return column_row, ordered_indices

    geojson_shape = geopandas.read_file(path_to_geojson)
    geojson_array = numpy.full((len(y_dim), len(x_dim)), False, dtype=bool)
    all_indicies = []

    if grid_mapping_variable is not None:
        geojson_crs = pyproj.crs.CRS(geojson_shape.crs)
        array_crs = _create_transform_crs(grid_mapping_variable)
    
        if geojson_crs != array_crs:
            geojson_shape = geojson_shape.to_crs(array_crs)
        
    shape = geojson_shape['geometry'][0]
    
    if shape.type == 'Point':
        coord = shape.coords[0]
        y_subtrace = abs(y_dim - coord[1])
        y_min = y_subtrace.min()
        y_index = numpy.where(y_subtrace == y_min)[0][0]
        
        x_subtrace = abs(x_dim - coord[0])
        x_min = x_subtrace.min()
        x_index = numpy.where(x_subtrace == x_min)[0][0]
        
        extents = (x_index, y_index)
        geojson_array = []
        
    else:
        for index, shape in enumerate(geojson_shape['geometry']):
            if shape.type == 'Polygon':
                column_row, indicies = outline_shape(shape)
                all_indicies.append(indicies)
                
                if not geojson_array[column_row[0], column_row[1]]:
                    counter, list_of_cells = fill_shape(column_row, 0, [])
                    for cell in list_of_cells:
                        if geojson_array[cell[0], cell[1]]:
                            list_of_cells.remove(cell)
                        else:
                            counter, list_of_cells = fill_shape(cell, 0, list_of_cells)
                            
                        geojson_array[cell[0], cell[1]] = True

            elif shape.type == 'MultiPolygon':
                for num, shp in enumerate(shape.geoms):
                    column_row, indicies = outline_shape(shp)
                    all_indicies.append(indicies)
    
                    if not geojson_array[column_row[0], column_row[1]]:
                        counter, list_of_cells = fill_shape(column_row, 0, [])
                        for cell in list_of_cells:
                            if geojson_array[cell[0], cell[1]]:
                                list_of_cells.remove(cell)
                            else:
                                counter, list_of_cells = fill_shape(cell, 0, list_of_cells)

        all_indicies_array = numpy.concatenate(all_indicies, axis=0)
        extents = (min(all_indicies_array[:,0]), max(all_indicies_array[:,0]), min(all_indicies_array[:,1]), max(all_indicies_array[:,1]))
        
    return geojson_array, extents
