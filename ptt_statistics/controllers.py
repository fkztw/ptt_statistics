import re
import datetime
from pprint import pprint

from pony import orm

from . import models


@orm.db_session
def store_board(board):
    board_entity = models.Board.get(name=board.name)

    if board_entity is None:
        board_entity = models.Board(name=board.name)

    # orm.show(board_entity)


@orm.db_session
def store_article(article, board):
    board_entity = models.Board.get(name=board.name)
    article_entity = models.Article.get(identifier=article.id,
                                        board=board_entity)

    if article_entity is None:
        user_id = (article.author.split()[0]
                   if isinstance(article.author, str)
                   else '')
        user_entity = models.User.get(identifier=user_id)
        if user_entity is None:
            user_entity = models.User(identifier=user_id)

        article_type = (article.type.strip()
                        if isinstance(article.type, str)
                        else '')
        article_type_entity = models.ArticleType.get(name=article_type,
                                                     board=board_entity)
        if article_type_entity is None:
            article_type_entity = models.ArticleType(name=article_type,
                                                     board=board_entity)

        article_title = (article.title.strip()
                         if isinstance(article.title, str)
                         else '')
        article_title_entity = models.ArticleTitle.get(name=article_title,
                                                       board=board_entity)
        if article_title_entity is None:
            article_title_entity = models.ArticleTitle(name=article_title,
                                                       board=board_entity)

        try:
            article_date = article.time.date()
            article_time = article.time.time()
        except (AttributeError, ValueError):
            article_date = None
            article_time = None

        article_entity = models.Article(identifier=article.id,
                                        url=article.url,
                                        user=user_entity,
                                        reply=bool(article.reply),
                                        type=article_type_entity,
                                        title=article_title_entity,
                                        date=article_date,
                                        time=article_time,
                                        content=article.content,
                                        board=board_entity,
                                        update_time=datetime.datetime.now())
        pprint(vars(article))
        orm.show(article_entity)
    else:
        article_entity.update_time = datetime.datetime.now()


@orm.db_session
def store_comment(comment, article, board):
    '''user, content, tag, time'''
    board_entity = models.Board.get(name=board.name)

    tag_entity = models.CommentTag.get(name=comment['tag'])
    if tag_entity is None:
        tag_entity = models.CommentTag(name=comment['tag'])

    user_entity = models.User.get(identifier=comment['user'])
    if user_entity is None:
        user_entity = models.User(identifier=comment['user'])

    comment_content_entity = models.CommentContent.get(s=comment['content'])
    if comment_content_entity is None:
        comment_content_entity = models.CommentContent(s=comment['content'])

    article_entity = models.Article.get(identifier=article.id,
                                        board=board_entity)

    try:
        comment_year = article_entity.date.year
    except AttributeError:
        comment_year = datetime.MAXYEAR

    m = re.match(r"(\d+/\d+)?\s*(\d+:\d+)?", comment['time'])
    comment_date, comment_time = m.groups()
    if comment_date:
        comment_month, comment_day = map(int, comment_date.split('/'))

        try:
            article_month = article_entity.date.month
        except AttributeError:
            pass
        else:
            if (
                article_month == 12 and
                comment_month == 1 and
                comment_year != datetime.MAXYEAR
            ):
                comment_year += 1
            elif comment_month < article_month:
                return

        try:
            comment_date = datetime.date(comment_year,
                                         comment_month,
                                         comment_day)
        except ValueError:
            comment_date = None
    if comment_time:
        comment_hour, comment_min = map(int, comment_time.split(':'))
        try:
            comment_time = datetime.time(comment_hour, comment_min)
        except ValueError:
            comment_time = None

    try:
        comment_entity = models.Comment.get(tag=tag_entity,
                                            user=user_entity,
                                            content=comment_content_entity,
                                            date=comment_date,
                                            time=comment_time,
                                            article=article_entity)
    except:
        import traceback
        traceback.print_exc()
        orm.show(tag_entity)
        orm.show(user_entity)
        orm.show(comment_content_entity)
        print(comment_date)
        print(comment_time)
        orm.show(article_entity)
        print(article_entity.url)

    if comment_entity is None:
        comment_entity = models.Comment(tag=tag_entity,
                                        user=user_entity,
                                        content=comment_content_entity,
                                        date=comment_date,
                                        time=comment_time,
                                        article=article_entity)

        pprint(comment.items())
        orm.show(comment_entity)


@orm.db_session
def get_specific_day_info(board_name, **kargs):
    pass


@orm.db_session
def get_specific_month_info(board_name, **kargs):
    pass


@orm.db_session
def get_specific_year_info(board_name, **kargs):

    articles = {}
    total_articles = orm.select(article for article in models.Article
                                if article.date.year == kargs['year']
                                and article.board.name == board_name)
    articles['total'] = total_articles.count()

    articles['months'] = {month: orm.count(article
                                           for article in total_articles
                                           if article.date.month == month)
                          for month in range(1, 13)}

    authors = {}
    authors['total'] = orm.count(article.user for article in total_articles)

    comments = {}
    total_comments = orm.select(comment
                                for comment in models.Comment
                                if comment.date.year == kargs['year']
                                and comment.article.board.name == board_name)
    tag_names = orm.select(tag.name for tag in models.CommentTag)
    comments['total'] = total_comments.count()
    comments['tags'] = {tag_name: orm.count(comment
                                            for comment in total_comments
                                            if comment.tag.name == tag_name)
                        for tag_name in tag_names}

    data = {}
    sub_dicts = ('articles', 'authors', 'comments')
    for sub_dict in sub_dicts:
        data[sub_dict] = eval(sub_dict)
    return data
