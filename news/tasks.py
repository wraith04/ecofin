from celery import shared_task
from news.models import User
from news.news_redis import cache_news_representation

from news.spider.ljyjh_update import lj_main
from news.spider.zgqj_update import zg_main
from news.spider.zycj_update import zy_main
from news.recommend_for_user import * # 导入你的推荐函数
from news.spider.sino_update import sino_main
from news.spider.ppxw_update import crawl_and_save_news


@shared_task
def cache_user_recommendations():
    for user in User.objects.all():
        print(user.id)
        recommendations = recommend_for_user(user.id)
        # 假设你有一个函数来缓存推荐结果
        cache_recommendations_for_user(user.id, recommendations)

@shared_task
def cache_all_news_representations():
    global keras_model, loaded_model, loaded_dictionary, tag_model, tag_encoder
    remodel = '/Users/jiebaibai/Downloads/eco_fin/news/my_model.keras'
    keras_model = load_model(remodel)
    model_dir = '/Users/jiebaibai/Downloads/eco_fin/news/models_data'
    loaded_model = LdaModel.load(os.path.join(model_dir, 'lda_model.model'))
    loaded_dictionary = Dictionary.load(os.path.join(model_dir, 'lda_dictionary.dict'))
    tags = [tag.tag_name for tag in Tag.objects.all().order_by('id')]
    tag_model, tag_encoder = create_category_feature_extractor(tags)
    for news in News.objects.all():
        try:
            # 尝试从缓存中获取推荐结果
            cache_key = f'news_representation_{news.id}'
            cached_recommendations = cache.get(cache_key)
            if cached_recommendations is not None:
                return
        # 生成新闻表示
            news_representation = create_news_representation(
                news, tag_model, tag_encoder, loaded_model, loaded_dictionary
            )
            cache_key = f'news_representation_{news.id}'
            print(news.id)
            cache.set(cache_key, news_representation, 604800)
        except Exception as e:
            print(f"Error in recommend_for_news: {e}")


# @shared_task
# def run_pp_spider():
#     crawl_news()
#
#
# @shared_task
# def run_sino_spider():
#     sino_main()
#
#
# @shared_task
# def run_lj_spider():
#     lj_main()
#
#
# @shared_task
# def run_zg_spider():
#     zg_main()
#
#
# @shared_task
# def run_zy_spider():
#     zy_main()
