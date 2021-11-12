"""--------------------------------------------------------------------------------------------
Implementação de métodos auxiliares
--------------------------------------------------------------------------------------------"""

#--------------------------------------- Imports --------------------------------------#
from copy import deepcopy

#--------------------------------------- Function -------------------------------------#
# Retorna os dados de um alimento cadastrado
def getFood(foodCode, foods, grouping):
    ingredient = deepcopy(next((food for food in foods if food["code"] == foodCode), None))
    ingredient = portionModifier([ingredient], grouping)[0]
    return ingredient

# Retorna um array com os dados dos alimentos a partir de um array dos códigos
def getFoods(items, foods, grouping, replaceable = False):
    foodMenu = []
    for foodCode in items:
        if (replaceable == True and foodCode["replaceable"] == True) or replaceable == False:
            food = getFood(foodCode["code"], foods, grouping).copy()
            if food == None:
                raise Exception("O alimento <" + str(foodCode["code"]) + "> não foi encontrado")
            else:
                foodMenu.append(food)
    return foodMenu

# Retorna um array com os alimentos não substituíveis do cardápio de entrada
def getNonReplaceableFood(items, foods):
    result = []
    for hit in items:
        if (hit["replaceable"] == False):
            food = getFood(hit["code"], foods).copy()
            if food == None:
                raise Exception("O alimento <" + str(hit["code"]) + "> não foi encontrado")
            else:
                result.append({"food": food, "score": 0})
    return result

# Retorna o agrupamento de um alimento
def getGrouping(foodCode, grouping):
    result = None
    for group in grouping:
        result = next((group for x in group["items"] if x["code"] == foodCode), None)
        if result != None:
            break
    return result

# Retorna um array com os agrupamentos que contém os alimentos do cardápio de entrada
# Premissa: Agrupamentos não possuem alimentos repetidos e um alimento está contido em 
# apenas 1 agrupamento 
def getGroupingMenu(items, grouping):
    groupingMenu = []
    for foodCode in items:
        group = getGrouping(foodCode["code"], grouping).copy()
        group["referenceFood"] = foodCode
        if group == None:
            raise Exception("O alimento <" + str(foodCode["code"]) + "> não possui agrupamento")
        else:
            groupingMenu.append(group)
    return groupingMenu
    
# Calcula as propriedades de um conjunto de alimentos
def calculateProperties(items):
    totalProtein = totalLipid = totalCarbo = totalCal = 0
    for food in items:
        totalProtein += float(food["protein"])
        totalLipid += float(food["lipid"])
        totalCarbo += float(food["carbo"])
        totalCal += float(food["calorie"])
    return {"totalProtein": totalProtein, "totalLipid": totalLipid, "totalCarbo": totalCarbo, "totalCal": totalCal}

# Calcula as propriedades de um conjunto de alimentos
def calculatePropertiesMeal(items, foods, grouping):
    mealmacro = []
    for meal in items:
        totalProtein = totalLipid = totalCarbo = totalCal = 0
        for item in meal['items']:
            ingredient = deepcopy(next((ingredient for ingredient in foods if ingredient['code'] == item['code']), None))
            ingredient = portionModifier([ingredient], grouping)[0]
            totalProtein += float(ingredient["protein"])
            totalLipid += float(ingredient["lipid"])
            totalCarbo += float(ingredient["carbo"])
            totalCal += float(ingredient["calorie"])
        mealmacro.append({'schooltype': meal['schooltype'],
                          'mealtype': meal['mealtype'],
                          'description': meal['description'],
                          'ingredients' : [ingredient['code'] for ingredient in meal['items']],
                          'macros':[{"totalProtein": totalProtein,
                                     "totalLipid": totalLipid,
                                     "totalCarbo": totalCarbo,
                                     "totalCal": totalCal}]})
    return mealmacro

# Retorna o índice do array da primeira ocorrência do elemento e -1 caso não exista
def findIndex(array, key, value):
    result = -1
    cont = 0
    for i in array:
        if i[key] == value:
            result = cont
            break
        cont = cont + 1 
    return result

# Método utilizado para ordenar a lista de substituições
def sort(array, key):
    return sorted(array, key=lambda x: x[key], reverse=False)

# Compara os itens e retorna o farol indicado, similarityList devem ser do tipo list
def computeColors(config, similarityList):
    dim = len(config['colors'])
    if dim == 0:
        colorsVector = ['NA']*len(similarityList)
    elif dim == 1:
        colorsVector = [config['colors'][0]]*len(similarityList)
    elif dim == 2:
        med = 1/dim
        colorsVector = [config['colors'][0] if score<=med else
                        config['colors'][1] for score in similarityList]
    elif dim == 3:
        lower = 1/dim
        upper = lower*2
        colorsVector = [config['colors'][0] if score<=lower else
                        config['colors'][1] if score<upper else
                        config['colors'][2] for score in similarityList]
    elif dim == 4:
        lower = 1/dim
        med = lower*2
        upper = lower*3
        colorsVector = [config['colors'][0] if score<=lower else
                        config['colors'][1] if score<=med else
                        config['colors'][2] if score<upper else
                        config['colors'][3] for score in similarityList]
    else:
        lower = 1/dim
        med = lower*2
        medupper = lower*3
        upper = lower*4
        colorsVector = [config['colors'][0] if score<=lower else
                        config['colors'][1] if score<=med else
                        config['colors'][2] if score<=medupper else
                        config['colors'][3] if score<upper else 
                        config['colors'][4] for score in similarityList]
    return colorsVector

# Remove pratos sem itens em estoque
def inventorychecker(meals, inventory):
    acc=0
    inventoryList = [inv['foodCode'] for inv in inventory]
    for meal in meals:
        if set(meal['ingredients']).issubset(inventoryList):
            acc += 1
        else:
            meals.pop(acc)
            acc += 1
    return meals

# Cria a matrix para comparação e lista de pratos respectivos
def matrixMaker(mealsgroup):
    candidatesMatrix = []
    meals = []
    for meal,data in mealsgroup.groupby(by=['description']):
            macros = data['macros'].values[0][0]
            meals.append(meal)
            candidatesMatrix.append([macros["totalCal"],macros["totalProtein"], macros["totalLipid"], macros["totalCarbo"]])
    
    return meals, candidatesMatrix

# Adapta as porções de 100g (TACO/POF) para novos valores, modifica as propriedades no campo foods
# Não funcional caso haja ingredientres com mais de um agrupamento
def portionModifier(foods, grouping):
    foodsCopy = deepcopy(foods)
    for food in foodsCopy:
        portion = next((elemts['gramsPortion'] for group in grouping for elemts in group['items'] if elemts['code'] == food['code']), None)
        if portion == None:
            raise Exception("Ingrediente não encontrado! COD do alimento: {}".format(food['code']))
        food['protein'] = food['protein']*(portion/100)
        food['lipid'] = food['lipid']*(portion/100)
        food['carbo'] = food['carbo']*(portion/100)
        food['calorie'] = food['calorie']*(portion/100) 
    return foodsCopy