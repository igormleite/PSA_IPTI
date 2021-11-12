"""--------------------------------------------------------------------------------------------
Implementação dos modelos responsáveis por gerar listas de substituições para cardápios
--------------------------------------------------------------------------------------------"""
import utils as utils
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial.distance import pdist, squareform
import numpy as np
import pandas as pd

"""
Método utilizado para gerar combinações com as substituições sugeridas para cada item de um
um cardápio de entrada.
"""
def menuGenerator(config, menuList, partialResult, foods):

    from itertools import product

    # Obtém os candidatos
    candidates = []
    for candidate in partialResult["itemReplacements"]:
        if len(candidate["replacements"]) > 0:
            candidates.append(candidate["replacements"])

    # Obtém os alimentos não substituíveis
    nonReplaceableFood = utils.getNonReplaceableFood(menuList["items"], foods)

    # Realiza a combinação entre os candidatos
    partialResult["menuReplacements"] = []
    for alternative in product(*candidates):
        alternative = list(alternative) + nonReplaceableFood
        # Calcula score do prato
        totalScore = 0
        for hit in alternative:
            totalScore += hit["score"]
        alternative = [x["food"] for x in alternative]
        # Calcula propriedades do prato
        properties = utils.calculateProperties(alternative)
        # Gera o resultado
        partialResult["menuReplacements"].append({"properties": properties, "menu": alternative, "totalScore": totalScore})
        partialResult["menuReplacements"] = utils.sort(partialResult["menuReplacements"], "totalScore")[0:config["limit"]]
    
    # Calcula o semáforo
    scoresVector = np.array([hit["totalScore"] for hit in partialResult["menuReplacements"]]).reshape([-1,1])
    scoresVector = MinMaxScaler().fit_transform(np.array(scoresVector)).tolist()
    scoresVector = [score[0] for score in scoresVector]
    colorsVector = utils.computeColors(config, scoresVector)
    for i in range(len(partialResult["menuReplacements"])):
        partialResult["menuReplacements"][i]["semaphore"] = colorsVector[i]
    
    return partialResult

"""
Método utilizado para gerar substituições dado um cardápio de entrada.

Este método gera uma matriz de similaridade de acordo com uma métrica definida (por exemplo uma
norma envolvendo os macronutrientes e valor energético) e com isso ordena as sugestões de substituição
de acordo com um critério definido.

Os alimentos sugeridos levam em consideração a disponibilidade de estoque e alimentos pertencentes
a um mesmo agrupamento.
"""
def similarityMatrix(config, menu, grouping, inventory, foods):

    # teste = {}

    # Obtém os alimentos marcados como substituíveis do cardápio de entrada
    replaceableFoodMenu = utils.getFoods(menu["items"], foods, grouping, replaceable = True)
    # teste["replaceableFoodMenu"] = replaceableFoodMenu
    # print(replaceableFoodMenu)

    # Verifica disponibilidade de estoque
    for item in replaceableFoodMenu:
        if utils.findIndex(inventory, "foodCode", item["code"]) == -1:
            raise Exception("O alimento " + item["name"] + " não possui disponibilidade de estoque")

    # Obtém todos os alimentos do cardápio de entrada
    foodMenu = utils.getFoods(menu["items"], foods, grouping, replaceable = False)
    # teste["foodMenu"] = foodMenu

    # Obtém os agrupamentos dos alimentos substituíveis do cardápio de entrada
    groupingMenu = utils.getGroupingMenu(replaceableFoodMenu, grouping)
    if len(groupingMenu) != len(replaceableFoodMenu):
        raise Exception("Quantidade de agrupamentos divergente da quantidade de alimentos do cardápio")
    # teste["groupingMenu"] = groupingMenu

    # Calcula as propriedades do cardápio de entrada
    properties = utils.calculateProperties(foodMenu)
    # teste["properties"] = properties
    
    # Define variável que será utilizada para armazenar o resultado do método
    result = {
        "inputMenu": {
            "properties": {
                "protein": properties["totalProtein"], 
                "lipid": properties["totalLipid"], 
                "carbo": properties["totalCarbo"],
                "calorie": properties["totalCal"]
            },
            "foods": [food["code"] for food in foodMenu]
        },
        "itemReplacements": []
    }

    # Variável para armazenar a índice de itemReplacements
    auxItemReplacements = 0
    
    # Gera lista de candidatos por agrupamento
    # Loop sobre cada agrupamento oriundo dos alimentos substituíveis do cardápio
    for group in groupingMenu:
        candidates = []
        for itemsGroup in group["items"]:
            food = utils.getFood(itemsGroup["code"], foods, grouping)
            if food == None:
                raise Exception("O alimento <" + str(itemsGroup["code"]) + "> não foi encontrado")
            else:
                candidates.append(food)
        # teste["candidates"] = candidates

        # Cria uma matriz apenas com as propriedades desejadas dos candidatos
        candidatesMatrix = []
        for candidate in candidates:
            candidatesMatrix.append([candidate["calorie"],candidate["protein"], candidate["lipid"], candidate["carbo"]])
    
        # Normaliza a matriz
        candidatesMatrixNorm = MinMaxScaler().fit_transform(candidatesMatrix)

        # Calcula a matriz de similaridade
        if (config["kernel"] == "linear"):
            kmodel = "cityblock"
        elif (config["kernel"] == "quadratico"):
            kmodel = "euclidean"
        elif (config["kernel"] == "cosseno"):
            kmodel = "cosine"
        else:
            kmodel = 'cityblock'
        similarityMatrix = squareform(
            pdist(candidatesMatrixNorm, 
                metric=kmodel, 
                w=np.array([
                    config["weights"]["calorie"],
                    config["weights"]["protein"],
                    config["weights"]["lipid"],
                    config["weights"]["carbo"]
                ])
            )
        )

        # Tratamento do resultado
        indexResult = utils.findIndex(candidates, "code", group["referenceFood"]["code"])

        if indexResult != -1:
            auxObj = []
            result["itemReplacements"].append({
                "item": group["referenceFood"],
                "replacements": []
            })
            for i in range(len(similarityMatrix[indexResult])):
                if candidates[i]["code"] != group["referenceFood"]["code"]:
                    auxObj.append({
                        "food": candidates[i], 
                        "score": similarityMatrix[indexResult][i],
                        "semaphore": utils.computeColors(config,[similarityMatrix[indexResult][i]])[0]
                    })
            result["itemReplacements"][auxItemReplacements]["replacements"] = utils.sort(auxObj, "score")[0:config["limit"]]
            auxItemReplacements = auxItemReplacements + 1
            # print (result)
        else:
            raise Exception("Alimento não encontrado na matriz de similaridade")
    
    # print(similarityMatrix)
    
    return result

def menuSuggester(config, menuList, grouping, inventory, foods):
    
    # Calcular macro dos pratos
    mealMacros = utils.calculatePropertiesMeal(menuList, foods, grouping)
    
    # Remover pratos cujos itens não estão em estoque
    mealMacros = utils.inventorychecker(mealMacros, inventory)
    
    # Identifica se existe substitutos para viáveis para a lista de pratos
    if len(mealMacros) == 1 or len(mealMacros) == 0:
            raise Exception("Alimento substutitos no cardápio com disponibilidade em estoque")
    # Transforma a lista de pratos em DataFrame
    mealMacros = pd.DataFrame(mealMacros)
    
    # Separa a comparação por tipo de escola e tipo de refeição
    result = []
    for (schooltype,mealtype),df in mealMacros.groupby(by=['schooltype', 'mealtype']):
        # Cria uma matriz com as propriedades desejadas dos candidatos
        mealList, candidatesMatrix = utils.matrixMaker(df)
        
        # Normaliza a matriz
        candidatesMatrixNorm = MinMaxScaler().fit_transform(candidatesMatrix)
        
        # Calcula a matriz de similaridade
        if (config["kernel"] == "linemealsgroupar"):
            kmodel = "cityblock"
        elif (config["kernel"] == "quadratico"):
            kmodel = "euclidean"
        elif (config["kernel"] == "cosseno"):
            kmodel = "cosine"
        else:
            kmodel = 'cityblock'
        similarityMatrix = squareform(
            pdist(candidatesMatrixNorm, 
                metric=kmodel, 
                w=np.array([
                    config["weights"]["calorie"],
                    config["weights"]["protein"],
                    config["weights"]["lipid"],
                    config["weights"]["carbo"]
                ])
            )
        )
        similarityMatrix = MinMaxScaler().fit_transform(similarityMatrix)
        # Listagem e ordenação dos resultados
        for i in range(len(mealList)):
            # Enumera os pratos e ordena de forma crescente pelo score
            auxObj = list(enumerate(similarityMatrix[i]))
            auxObj = utils.sort(auxObj, 1)[1:config["limit"]+1]
            # Normalização dos scores
            # Função "computeLights" requer o recebimento de uma lista
            colors = utils.computeColors(config, similarityMatrix[i].tolist())
            suggestions = []
            for ii in auxObj:
                # Agrupa as listas de sugestões para os pratos 
                suggestions.append({'description':mealList[ii[0]],
                                    'score':ii[1],
                                    'semaphore':colors[ii[0]]})
            #Agrupa as sugestões como função da Escola, tipo de refeição, prato e sugestões
            result.append({'schooltype': schooltype,
                           'mealtype': mealtype,
                           'description':mealList[i],
                           'menuReplacements':suggestions})
    
    return result