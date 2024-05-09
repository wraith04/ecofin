
import os

import numpy as np
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from django.core.cache import cache
from django.utils.timezone import now, timedelta
from news.models import UserBehavior, News, Tag
from keras.models import load_model
from news.re_model.features_extractors import create_category_feature_extractor
from news.re_model.news_representation import create_news_representation
from news.re_model.user_representation import generate_user_representation
from news.re_model.prediction_models import create_user_click_prediction_model


def preload_resources():
    """预加载资源，例如模型和字典。"""
    global keras_model, loaded_model, loaded_dictionary, tag_model, tag_encoder
    remodel = '/Users/jiebaibai/Downloads/eco_fin/news/my_model.keras'
    keras_model = load_model(remodel)
    model_dir = '/Users/jiebaibai/Downloads/eco_fin/news/models_data'
    loaded_model = LdaModel.load(os.path.join(model_dir, 'lda_model.model'))
    loaded_dictionary = Dictionary.load(os.path.join(model_dir, 'lda_dictionary.dict'))
    tags = [tag.tag_name for tag in Tag.objects.all().order_by('id')]
    tag_model, tag_encoder = create_category_feature_extractor(tags)


def get_filtered_news():
    """获取过滤后的新闻，比如最近一个月的热门新闻。"""
    one_month_ago = now() - timedelta(days=30)
    recent_news = News.objects.filter(publish_date__gte=one_month_ago).order_by('-reads')[:1000]
    return recent_news


def get_cached_representation(key, generation_function, *args):
    """从缓存中获取表示，如果未命中，则生成并缓存。"""
    representation = cache.get(key)
    if representation is None:
        representation = generation_function(*args)
        cache.set(key, representation, 86400)  # 缓存24小时
    return representation


def cache_recommendations_for_user(user_id, recommendations):
    """
    缓存用户的推荐结果。

    :param user_id: 用户ID。
    :param recommendations: 推荐结果列表，通常包含推荐新闻的ID。
    """
    cache_key = f'user_recommendations_{user_id}'
    # 缓存24小时。86400秒等于24小时
    cache.set(cache_key, recommendations, 86400)


def recommend_for_user(user_id):
    """根据用户ID生成新闻推荐。"""
    max_sequence_length = 100  # 最大序列长度
    news_vector_dimension = 794  # 新闻向量维度
    try:
        # 尝试从缓存中获取推荐结果
        cache_key = f'user_recommendations_{user_id}'
        cached_recommendations = cache.get(cache_key)

        # 如果缓存中已有推荐结果，直接返回这些结果
        if cached_recommendations is not None:
            return cached_recommendations

        # 如果没有缓存的推荐结果，继续执行推荐逻辑
        user_behaviors = UserBehavior.objects.filter(user=user_id)
        if user_behaviors.count() < 20:
            recommended_news = News.objects.order_by('-reads').values_list('id', flat=True)[:6]
            return list(recommended_news)

        user_representation_key = f'user_representation_{user_id}'
        user_representation = get_cached_representation(
            user_representation_key,
            generate_user_representation,
            user_behaviors, create_news_representation,tag_model, tag_encoder, loaded_model, loaded_dictionary,max_sequence_length,
            news_vector_dimension
        )

        predictions = []
        filtered_news = get_filtered_news()

        for news in filtered_news:
            news_representation_key = f'news_representation_{news.id}'
            news_representation = get_cached_representation(
                news_representation_key,
                create_news_representation,
                news, tag_model, tag_encoder, loaded_model, loaded_dictionary
            )

            news_representation_reshaped = np.expand_dims(news_representation, axis=0)
            user_representation_expanded = np.repeat(np.array([user_representation]),
                                                     news_representation_reshaped.shape[0], axis=0)
            prediction = keras_model.predict([user_representation_expanded, news_representation_reshaped])[0][0]
            predictions.append((news.id, prediction))

        predictions.sort(key=lambda x: x[1], reverse=True)
        recommended_news_ids = [pred[0] for pred in predictions[:5]]
        cache_recommendations_for_user(user_id, recommended_news_ids)
        return recommended_news_ids
    except Exception as e:
        print(f"Error in recommend_for_user: {e}")
        return []
