from keras.layers import Input, Flatten, Dense, Dot,Activation
from keras.models import Model
def create_user_click_prediction_model(news_vector_dim, user_vector_dim):
    # 定义输入层
    user_input = Input(shape=(user_vector_dim,), name='user_input')
    news_input = Input(shape=(1, news_vector_dim), name='news_input')  # 假设新闻输入是(None, 1, 794)形状
    news_input_flattened = Flatten()(news_input)  # 将输入扁平化以匹配预期的形状
    news_input_adjusted = Dense(user_vector_dim)(news_input_flattened)
    # 计算向量内积
    dot_product = Dot(axes=-1)([user_input, news_input_adjusted])

    # 使用sigmoid激活函数来输出点击概率
    output = Activation('sigmoid')(dot_product)

    # 构建和编译模型
    model = Model(inputs=[user_input, news_input], outputs=output)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    return model
