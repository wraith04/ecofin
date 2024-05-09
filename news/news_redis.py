import os
from news.re_model.features_extractors import create_category_feature_extractor
from news.re_model.news_representation import create_news_representation
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from django.core.cache import cache
from django.utils.timezone import now, timedelta
from news.models import News, Tag
from keras.models import load_model


def cache_news_representation(news_id, expiration=604800):
    """
    缓存指定新闻的表示。

    :param news_id: 新闻的ID。
    :param expiration: 缓存过期时间，以秒为单位，默认为一周（604800秒）。
    """
    remodel = '/Users/jiebaibai/Downloads/eco_fin/news/my_model.keras'
    keras_model = load_model(remodel)
    model_dir = '/Users/jiebaibai/Downloads/eco_fin/news/models_data'
    loaded_model = LdaModel.load(os.path.join(model_dir, 'lda_model.model'))
    loaded_dictionary = Dictionary.load(os.path.join(model_dir, 'lda_dictionary.dict'))
    tags = [tag.tag_name for tag in Tag.objects.all().order_by('id')]
    tag_model, tag_encoder = create_category_feature_extractor(tags)
    # 尝试获取新闻对象
    try:
        news = News.objects.get(id=news_id)
    except News.DoesNotExist:
        print(f"News with id {news_id} does not exist.")
        return

    # 生成新闻表示
    news_representation = create_news_representation(
        news, tag_model, tag_encoder, loaded_model, loaded_dictionary
    )
    print(news_id)
    # 定义缓存键
    cache_key = f'news_representation_{news_id}'

    # 将新闻表示存入缓存
    cache.set(cache_key, news_representation, expiration)
