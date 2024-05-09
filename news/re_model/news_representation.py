from news.re_model.features_extractors import *


def create_news_representation(news,tag_model,tag_encoder,loaded_model,loaded_dictionary):
    title_vector = text_feature_extractor(news.title)  # 转换标题文本为向量
    content_vector = lda_topic_feature_extractor(loaded_model, news.content, loaded_dictionary)
    content_vector = np.expand_dims(content_vector, axis=0)  # 从(m,)变为(1, m)

    # 类别特征提取，确保是二维数组
    tag_vector = get_category_feature(tag_model, tag_encoder, news.news_tag_id)
    if tag_vector.ndim == 1:
        tag_vector = np.expand_dims(tag_vector, axis=0)  # 从(n,)变为(1, n)

    # 确保所有数组都是二维的后进行拼接
    news_representation = np.concatenate([title_vector, content_vector, tag_vector], axis=-1)
    # news_representation_flat = news_representation.flatten()
    return news_representation