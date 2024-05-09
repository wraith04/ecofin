from transformers import DistilBertTokenizer, DistilBertModel
import torch
import re
from keras.layers import Input, Embedding, Flatten, Dense
from sklearn.preprocessing import LabelEncoder
import numpy as np
from keras.models import Model
import os
model_path = '/Users/jiebaibai/Downloads/eco_fin/news/distilbert-base-uncased'
tokenizer, model = None, None
if os.path.exists(model_path):
    print("Path exists.")
    tokenizer = DistilBertTokenizer.from_pretrained(model_path)
    model = DistilBertModel.from_pretrained(model_path)
else:
    print("Path does not exist.")

def text_feature_extractor(text):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', text)
    inputs = tokenizer(cleantext, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    last_hidden_states = outputs.last_hidden_state
    text_vector = torch.mean(last_hidden_states, dim=1).numpy()
    return text_vector

# 类别特征提取
def get_category_feature(tag_model, tag_encoder, tag_id):
    tag_id=tag_id-1
    if tag_id not in range(len(tag_encoder.classes_)):
        raise ValueError("Tag ID is out of range.")
    tag_index = np.array([[tag_id]])
    category_feature = tag_model.predict(tag_index)
    return category_feature

# 主题特征提取
def lda_topic_feature_extractor(lda_model, text, dictionary):
    bow = dictionary.doc2bow(text.lower().split())
    topic_distribution = lda_model.get_document_topics(bow, minimum_probability=0)
    topic_vector = np.zeros(lda_model.num_topics)
    for index, prob in topic_distribution:
        topic_vector[index] = prob
    return topic_vector

# 创建类别特征提取器
def create_category_feature_extractor(tags, embedding_dim=8, output_dim=16):
    encoder = LabelEncoder()
    encoder.fit(tags)
    num_tags = len(encoder.classes_)
    category_input = Input(shape=(1,), name='category_input')
    category_embedding = Embedding(input_dim=num_tags, output_dim=embedding_dim, input_length=1, name='category_embedding')(category_input)
    category_embedding_flattened = Flatten()(category_embedding)
    output_layer = Dense(output_dim, activation='relu')(category_embedding_flattened)
    model = Model(inputs=category_input, outputs=output_layer)
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model, encoder