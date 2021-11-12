#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------- Imports --------------------------------------#
from methods import menuGenerator, similarityMatrix, menuSuggester, findSuggest
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
        
        # Cria a matrix de similaridade para cada agrupamento, nº saída igual (nº de agrupamentos x Nº itens dentro dos agrupamentos)
        suggest = similarityMatrix(config, grouping, foods)
        
        # Loop para cada item da matriz de similaridade
        for item in tqdm(suggest):
            outputFile = open("output/outputFile-item-" + item["nameReference"].replace(' ','_') + '_' + item["group"] +".json", "w", encoding = 'utf-8')
            outputFile = json.dump(item, outputFile, ensure_ascii = False)
        
        # Gera lista de sugestões alternativas, utilizado devido a indisponibilidade de estoque
        outputFile = open("output/altertiveOutputFile.json", "w", encoding = 'utf-8')
        outputFile = json.dump(menuSuggester(config, menuList, grouping, inventory, foods), outputFile, ensure_ascii = False)
    elif config["method"] == "exhaustiveSearch":
        print("exhaustiveSearch")
    else:
        print("Método inválido")

    # print(inputData)