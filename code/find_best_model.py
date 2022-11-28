import os

def find_best(path):
	
    re = {}
 
    for filename in os.listdir(path):
        if filename.endswith('.index'):
            data = os.path.splitext(filename)[0].split('-')
            re[str(data[0])] = str(data[-1])

    min_mape = min([float(v) for k, v in re.items()])
    epoch = [k for k, v in re.items() if float(v)==min_mape][-1]
    
    best = str(epoch) + '-' + str(min_mape)
    best_model_path =  path + f'/{best}'
    
    Best_model_file = open('Best_model.txt', "w")
    Best_model_file.write(best_model_path)
    Best_model_file.close()

    return best

if __name__=="__main__":
    
    path = './modelCheckpoints/dataset_snowyowl_final'

    find_best(path)