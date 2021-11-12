#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------- Imports --------------------------------------#
from methods import menuGenerator, similarityMatrix, menuSuggester
import json
from tqdm import tqdm

#---------------------------------------- Main ----------------------------------------#
if __name__ =="__main__":

    # Leitura do arquivo de entrada
    inputFile = open("inputData.json", encoding = 'utf-8')
    inputData = json.load(inputFile)
    inputFile.close()

    # Principais variáveis
    config     = inputData["config"]    # Configurações básicas para execução do método
    menuList   = inputData["menuList"]  # Cardápios de entrada
    grouping   = inputData["grouping"]  # Agrupamento dos alimentos
    inventory  = inputData["inventory"] # Disponibilidade de estoque
    foods      = inputData["foods"]     # Cadastro de alimentos

    if config["method"] == "similarityMatrix":
        # result = []

        # Loop para cada cardápio de entrada
        # section = [menuList[i] for i in [0,10,20,43]]
        # for menu in tqdm(section):
        for menu in tqdm(menuList[0:5]):
            partialResult = similarityMatrix(config, menu, grouping, inventory, foods)
            partialResult = menuGenerator(config, menu, partialResult, foods)
            outputFile = open("output/outputFile-meal-" + menu["description"].replace(':','') + ".json", "w", encoding = 'utf-8')
            outputFile = json.dump(partialResult, outputFile, ensure_ascii = False)
        
        # Gera lista de sugestões alternativas, utilizado devido a indisponibilidade de estoque
        outputFile = open("output/completeMeal.json", "w", encoding = 'utf-8')
        outputFile = json.dump(menuSuggester(config, menuList, grouping, inventory, foods), outputFile, ensure_ascii = False)
    elif config["method"] == "exhaustiveSearch":
        print("exhaustiveSearch")
    else:
        print("Método inválido")

    # print(inputData)