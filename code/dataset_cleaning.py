import os
import glob
import shutil

def clean_data(path, sample_ID):
    ''' 
    This function deletes some samples from the dataset.
    Args:
        path (str): The location of the dataset to be clean 
        sample_ID (int) : ID of the zip file containing the 10 samples to be removed
       
    '''
   
    path_new = 'training_snowyowl/results/dataset_snowyowl_final' # path of the final dataset
    graphs_path = "graphs"
    routings_path = "routings"

    # Create folders
    if (os.path.isdir(path_new)):
        print ("Destination path already exists. Files within the directory may be overwritten.")
    else:
        os.makedirs(path_new)
        os.makedirs(os.path.join(path_new, graphs_path))
        os.mkdir(os.path.join(path_new, routings_path))

    
    src_graph_path = path + '/graphs/'
    src_routing_path =  path + '/routings/'

    dst_graph_path = os.path.join(path_new, graphs_path)
    dst_routing_path = os.path.join(path_new, routings_path)

    #copy all traffic to the new dataset except the one to clean
    for file in glob.glob(os.path.join(path, "*.tar.gz")):
        d = file.split('.')[0].split('_')[-1]
        if int(d) // 10 != sample_ID:
            shutil.copy2(file, path_new)


    # copy all graphs to the new dataset except the one to clean
    for file in glob.glob(os.path.join(src_graph_path, "*.txt")):
        d = file.split('_')
        if d[-2] != str(sample_ID):
            shutil.copy2(file, dst_graph_path)

 
     # copy all routings to the new dataset except the one to clean
    list_paths = [x[0] for x in os.walk(src_routing_path)]
    for routing_path in list_paths[1:]:
        if routing_path[-3] != str(sample_ID):
            routing_sample = routing_path.split('/')[-1]
            s_path = dst_routing_path + "/" + routing_sample
            shutil.copytree(routing_path, s_path, dirs_exist_ok=True)


if __name__=="__main__":
    # Clean dataset
    print('Start data cleaning ...')
    path = 'training_snowyowl/results/dataset_snowyowl'
    sample_ID = 6
    clean_data(path, sample_ID)
    print(' Data cleaning Done! the final dataset name is: dataset_snowyowl_final')
    
    
    