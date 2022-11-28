from RouteNet_Fermi import evaluate

with open('Best_model.txt') as f:
    dir_model = f.readlines()[0]

MAPE = evaluate(dir_model)

print(f'MAPE = {MAPE}')