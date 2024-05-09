# import os
# import time
#
# import numpy as np
# from gensim.corpora import Dictionary
# from gensim.models import LdaModel
# from news.models import UserBehavior, News, Tag
# from keras.models import load_model
#
# from news.re_model.features_extractors import create_category_feature_extractor
# from news.re_model.news_representation import create_news_representation
# from news.re_model.user_representation import generate_user_representation
# from news.re_model.prediction_models import create_user_click_prediction_model
# # 假设模型已经被训练并保存
#
# def recommend_for_user(user_id):
#     """
#     根据用户ID生成新闻推荐。
#     """
#     try:
#         # 检查是否有足够的用户历史行为
#         user_behaviors = UserBehavior.objects.filter(user=user_id)
#         if user_behaviors.count() < 20:
#             # 如果历史行为不足，返回基于阅读量的推荐
#             recommended_news = News.objects.order_by('-reads').values_list('id', flat=True)[:5]
#             return list(recommended_news)
#         remodel = '/Users/jiebaibai/Downloads/eco_fin/news/my_model.keras'
#         keras_model = load_model(remodel)
#         model_dir = '/Users/jiebaibai/Downloads/eco_fin/news/models_data'
#         loaded_model = LdaModel.load(os.path.join(model_dir, 'lda_model.model'))
#         loaded_dictionary = Dictionary.load(os.path.join(model_dir, 'lda_dictionary.dict'))
#         tags = [tag.tag_name for tag in Tag.objects.all().order_by('id')]
#         tag_model, tag_encoder = create_category_feature_extractor(tags)
#         max_sequence_length = 100  # 最大序列长度
#         news_vector_dimension = 794  # 新闻向量维度
#         # 生成用户表示
#         # 生成用户表示
#         user_representation_start = time.time()
#         user_representation = generate_user_representation(
#             user_behaviors,
#             create_news_representation,
#             tag_model,
#             tag_encoder,
#             loaded_model,
#             loaded_dictionary,
#             max_sequence_length,
#             news_vector_dimension
#         )
#         user_representation_end = time.time()
#         print(f"生成用户表示时间：{user_representation_end - user_representation_start}秒")
#
#         # 打印用户表示以检查
#         print("User Representation:", user_representation)
#
#         # 初始化预测列表
#         predictions = []
#
#         # 获取所有新闻
#         all_news = News.objects.all()
#         prediction_start = time.time()
#         # 对于每条新闻，生成表示并预测点击概率
#         for news in all_news:
#             news_representation = create_news_representation(news, tag_model, tag_encoder, loaded_model,
#                                                              loaded_dictionary)
#
#             # 修正：添加一个额外的维度来匹配模型的期待输入形状
#             news_representation_reshaped = np.expand_dims(news_representation, axis=0)
#
#             # 重复用户表示以匹配新闻表示的批次大小
#             user_representation_expanded = np.repeat(user_representation[np.newaxis, :],
#                                                      news_representation_reshaped.shape[0], axis=0)
#
#             # 进行预测
#             prediction = keras_model.predict([user_representation_expanded, news_representation_reshaped])
#
#             # 添加预测结果
#             predictions.append((news.id, prediction[0][0]))
#         prediction_end = time.time()
#         print(f"预测时间：{prediction_end - prediction_start}秒")
#         sort_start = time.time()
#         # 根据预测的点击概率排序，选出排名最高的新闻
#         predictions.sort(key=lambda x: x[1], reverse=True)
#         recommended_news_ids = [pred[0] for pred in predictions[:5]]
#         sort_end = time.time()
#         print(f"排序时间：{sort_end - sort_start}秒")
#         # 返回推荐的新闻ID
#         return recommended_news_ids
#
#         return recommended_news_ids
#     except Exception as e:
#         print(f"Error in recommend_for_user: {e}")
#         return []
