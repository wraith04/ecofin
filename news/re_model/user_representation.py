import numpy as np
from keras.src.layers import GlobalAveragePooling1D
from keras.layers import Input, Dense, GRU
from keras.models import Model


def get_user_history_vectors(user_behaviors, create_news_representation, tag_model, tag_encoder, loaded_model,
                             loaded_dictionary):
    user_history_vectors = []
    for behavior in user_behaviors:
        news = behavior.news
        if news:
            news_vector = create_news_representation(news, tag_model, tag_encoder, loaded_model, loaded_dictionary)
            user_history_vectors.append(news_vector)
    return np.array(user_history_vectors)


def generate_user_representation(user_behaviors, create_news_representation, tag_model, tag_encoder, loaded_model,
                                 loaded_dictionary, max_sequence_length, news_vector_dimension):
    user_history_vectors = get_user_history_vectors(user_behaviors, create_news_representation, tag_model, tag_encoder,
                                                    loaded_model, loaded_dictionary)

    # 如果用户历史行为少于max_sequence_length，用0填充
    if len(user_history_vectors) < max_sequence_length:
        padding_length = max_sequence_length - len(user_history_vectors)
        padding = np.zeros((padding_length, 1, news_vector_dimension))
        user_history_vectors = np.vstack([padding, user_history_vectors])
    elif len(user_history_vectors) > max_sequence_length:
        user_history_vectors = user_history_vectors[-max_sequence_length:]

    # 定义GRU模型来处理序列数据
    sequence_input = Input(shape=(max_sequence_length, news_vector_dimension))
    gru_out = GRU(128, return_sequences=True)(sequence_input)

    # 应用注意力机制
    attention_probs = Dense(1, activation='softmax', name='attention_vec')(gru_out)
    attention_mul = attention_probs * gru_out
    attention_mul = GlobalAveragePooling1D()(attention_mul)

    # 定义模型
    user_interest_model = Model(inputs=[sequence_input], outputs=attention_mul)
    user_history_vectors_squeezed = np.squeeze(user_history_vectors, axis=1)
    # 生成用户表示
    print(user_history_vectors_squeezed.shape)

    # 然后，你可以像之前那样用它来进行预测
    user_representation = user_interest_model.predict(np.array([user_history_vectors_squeezed]))[0]
    return user_representation
