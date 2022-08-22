# 감성분석에 따른 음악 추천 알고리즘


## Emotion_classification
- 입력 값으로 받은 사용자의 문장을 6개의 라벨(분노/긴장/슬픔/평화/기쁨/중립)을 기준으로 Multi-class sentiment classification을 통해 감정을 분류합니다.  

- 학습에 사용되는 데이터는 AI-HUB 감성대화 말뭉치와 한국어 감정 정보가 포함된 단발성 대화 데이터셋입니다.  

- 모델로 사용될 후보군은 다음과 같습니다.
    - KcBert
    - Klue-RoBERTa-base
    - Kc-Electra
    - KoBERT

## Lyrics_croll
- 카카오 아레나(https://arena.kakao.com/c/8) 데이터를 DB를 곡 제목을 기준으로 멜론 웹사이트를 통해 가사를 수집합니다.
- 가사 내용을 기준으로 감성분석을 진행하여 해당 곡이 어떠한 감성(분노/긴장/슬픔/평화/기쁨/중립)에 가까운지 라벨링한다.

## MEL
- 카카오 아레나(https://arena.kakao.com/c/8)의 Mel-spectrogram data를 사용하여 멜로디 패턴에서 감성을 찾습니다. 
- Mel data에 라벨링하는 과정은 다음과 같습니다.  
    1. 해당 곡의 Mel-spectrogram data는 가사내용의 감성과 동일한 시너지를 낸다고 가정한다. (ex.가사내용과 상반되는 멜로디는 가정에서 배제)
    2. 라벨링된 Mel-spectrogram data를 기준으로 비슷한 형태를 띄는 다른 Mel spectrogram data에 Active learning을 적용하여 라벨링 한다.

## Recommendation
- 추천 시스템 작동과정  
    1. 사용자는 지금의 상태나 느낌을 문장으로 표현한다.
    2. Emotion_classification으로 입력받은 문장에 대해 감성분석을 진행하여 softmax의 마지막 벡터(1,6)을 추출한다.
    3. 추론된 벡터(1,6)과 가장 가까운 유사도를 가지는 Mel-spectrogram data를 분석한다.
    
