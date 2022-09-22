#-*- coding:utf-8 -*- 
import warnings
warnings.filterwarnings(action='ignore')
import time 
import sys
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import time
import torch
from transformers import AutoTokenizer,AutoModelForSequenceClassification,TextClassificationPipeline,pipeline,AutoModel
import os
os.environ['XRT_TPU_CONFIG'] = "localservice;0;localhost:51011"


# load model, tokenizer, pipline setting
num_labels = 6
model = AutoModelForSequenceClassification.from_pretrained("JUNEYEOB/FT_batch32_lyric_con_sent",num_labels=num_labels)
tokenizer = AutoTokenizer.from_pretrained('klue/roberta-large')
pipe  = pipeline("text-classification", model=model, tokenizer=tokenizer, return_all_scores = True)


label_name = {0:'기쁨',1:'긴장',2:'평화',3:'슬픔',4:'분노',5:'중립'}

# input = input("당신의 기분을 글로 표현해주세요! : ") # inference 문장

# start = time.time()
def emotion_analysis(input):
    emotion,em_list = [],[]
    for i in pipe(input):
        for j in range(len(i)):
            emotion.append(i[j]['score'])
    emotion = np.array(emotion).reshape(1,-1)

    for i in np.argsort(emotion[0])[::-1]:
        em_list.append(label_name[i])
    print(f'내가생각하는 당신은 {em_list}')
    print('당신에게 알맞는 노래 분석중 ----***')
    print('\n')
    return emotion,em_list

# data load 
data = pd.read_csv('database.csv')
data['lyric_label'] = data.lyric_label.apply(lambda x: np.array(eval(x)).reshape(1,-1))
data['mel_label'] = data.mel_label.apply(lambda x: np.array(eval(x)).reshape(1,-1))

#lyric + mel vector
def weighted_sum(datas,a=.5,b=.5):

    fin_vec = np.empty((0,6))
    for i in range(len(datas)):
        wei_vec = a*datas.lyric_label[i] + b*datas.mel_label[i]
        fin_vec = np.vstack((fin_vec,wei_vec))
    return fin_vec
vectors = weighted_sum(data)


def cos_sim(datas):
    cosine = []
    n= 0
    for i,j in enumerate(datas):
        j = j.reshape(1,-1)
        cosine_sim = cosine_similarity(emotion,j)
        cosine.append((i,cosine_sim))
    resys = sorted(cosine,key=lambda x:x[1],reverse=True)[:5]
        

    for i in resys:
        n = i[0]
        artist = data.iloc[n]['artist']
        song = data.iloc[n]['song_name']
        vec = vectors[n]
        #메인 라벨 3개 출력
        labels = []
        label_num = np.argsort(vec)[::-1]
        for j in label_num[:3]:
            label = label_name[j]
            labels.append(label)
    # return artist,song,labels
        print(f'가수:{artist} 곡:{song}') 
        print(f'주요감정{labels}')
        print(f'벡터값{vec}')
        print('\n')
        
rep='Y'

if __name__=="__main__":
    while rep =='y'or rep=='Y':
        start = time.time()
        str = input("당신의 기분을 글로 표현해주세요! : ")
        # a,b =  map(float,input().split())
        emotion,em_list = emotion_analysis(str)
        cos_sim(vectors)
        # cos_sim(vectors,a=a,b=b)
        end = time.time()
        print(f"{end - start:.5f} sec")
        rep = input("새로 문장 입력하시겠어요? : Y/N ")

    print('이용해주셔서 감사합니다.')