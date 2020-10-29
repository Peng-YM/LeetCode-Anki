import logging
import pathlib

from peewee import *

from utils import parser

if parser.get("DB", "debug") == "True":
    # logger
    logger = logging.getLogger('peewee')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

# connect or create the database
directory = parser.get("DB", "path")
p = pathlib.Path(directory)
p.mkdir(parents=True, exist_ok=True)
database = SqliteDatabase(directory + "/LeetCode.sqlite")


# data models
class BaseModel(Model):
    class Meta:
        database = database


class Problem(BaseModel):
    display_id = IntegerField(unique=True)
    level = CharField()
    title = CharField()
    slug = CharField(unique=True)
    description = TextField()
    accepted = BooleanField()

    # find the tags related to this question
    @property
    def tags(self):
        return (
            Tag.select().join(
                ProblemTag, on=Tag.slug == ProblemTag.tag
            ).where(
                ProblemTag.problem == self.id
            )
        )

    @property
    def solution(self):
        return (
            Solution.select().where(
                Solution.problem == self.id
            )
        )


class Submission(BaseModel):
    slug = ForeignKeyField(Problem, 'slug', backref='submissions')
    language = CharField()
    source = TextField()
    created = DateField()


class Tag(BaseModel):
    name = CharField()
    slug = CharField(unique=True, primary_key=True)

    @property
    def problems(self):
        return (
            Problem.select().join(
                ProblemTag, on=Problem.id == ProblemTag.problem
            ).where(
                ProblemTag.tag == self.slug
            ).order_by(
                Problem.id
            )
        )


class ProblemTag(BaseModel):
    problem = ForeignKeyField(Problem)
    tag = ForeignKeyField(Tag)

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('problem', 'tag'), True),
        )


class Solution(BaseModel):
    problem = ForeignKeyField(Problem, primary_key=True)
    content = TextField()
    url = CharField()


def create_tables():
    with database:
        database.create_tables([Problem, Solution, Submission, Tag, ProblemTag])


if __name__ == '__main__':
    create_tables()
