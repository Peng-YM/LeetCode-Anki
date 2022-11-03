import json
import os.path
import pickle
import re
from sys import exit

import requests
from requests.cookies import RequestsCookieJar
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from database_cn import Problem, ProblemTag, Tag, Submission, create_tables, Solution
from utils import destructure, random_wait, do, get

COOKIE_PATH = "./cookies_cn.dat"


class LeetCodeCrawler:
    def __init__(self):
        # create an http session
        self.session = requests.Session()
        self.session.headers.update(
            {
                'Host': 'leetcode.cn',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://leetcode.cn/accounts/login/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                'Connection': 'keep-alive'
            }
        )

    def login(self):
        browser_cookies = {}
        if os.path.isfile(COOKIE_PATH):
            with open(COOKIE_PATH, 'rb') as f:
                browser_cookies = pickle.load(f)
        else:
            print("😎 Starting browser login..., please fill the login form")
            browser = webdriver.Chrome(executable_path="./vendor/chromedriver")
            try:
                # browser login
                login_url = "https://leetcode.cn/accounts/login"
                browser.get(login_url)

                WebDriverWait(browser, 24 * 60 * 3600).until(
                    lambda driver: driver.current_url.find("login") < 0
                )
                browser_cookies = browser.get_cookies()
                with open(COOKIE_PATH, 'wb') as f:
                    pickle.dump(browser_cookies, f)
                print("🎉 Login successfully")

            except Exception as e:
                print(f"🤔 Login Failed: {e}, please try again")
                exit()

        cookies = RequestsCookieJar()
        for item in browser_cookies:
            cookies.set(item['name'], item['value'])

            if item['name'] == 'csrftoken':
                self.session.headers.update({
                    "x-csrftoken": item['value']
                })

        self.session.cookies.update(cookies)

    def fetch_accepted_problems(self):
        response = self.session.get("https://leetcode.cn/api/problems/all/")
        all_problems = json.loads(response.content.decode('utf-8'))
        # filter AC problems
        counter = 0
        for item in all_problems['stat_status_pairs']:
            if item['status'] == 'ac' and item['paid_only'] == False:
                id, slug = destructure(item['stat'], "question_id", "question__title_slug")
                # only update problem if not exists
                if Problem.get_or_none(Problem.id == id) is None:
                    counter += 1
                    # fetch problem
                    do(self.questionData, args=[slug, True])
                    # fetch solution
                    do(self.fetch_questionSolutionArticles, args=[slug])


                # always try to update submission
                # do(self.fetch_submission, args=[slug])
                do(self.fetch_lastSubmission, args=[slug])
        print(f"🤖 Updated {counter} problems")

    def questionData(self, slug, accepted=False):
        print(f"🤖 Fetching problem: https://leetcode.cn/problems/{slug}/...")
        query_params = {
            "operationName":"questionData",
            "variables":{
                "titleSlug":slug
            },
            "query":"query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    categoryTitle\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    envInfo\n    book {\n      id\n      bookName\n      pressName\n      source\n      shortDescription\n      fullDescription\n      bookImgUrl\n      pressImgUrl\n      productUrl\n      __typename\n    }\n    isSubscribed\n    isDailyQuestion\n    dailyRecordStatus\n    editorType\n    ugcQuestionId\n    style\n    exampleTestcases\n    __typename\n  }\n}\n"
        }

        resp = self.session.post(
            "https://leetcode.cn/graphql",
            data=json.dumps(query_params).encode('utf8'),
            headers={
                "content-type": "application/json",
            })
        body = json.loads(resp.content)

        # parse data
        question = get(body, 'data.question')

        Problem.replace(
            id=question['questionId'], display_id=question['questionFrontendId'], title=question["translatedTitle"],
            level=question["difficulty"], slug=slug, description=question['translatedContent'],
            accepted=accepted
        ).execute()

        for item in question['topicTags']:
            if Tag.get_or_none(Tag.slug == item['slug']) is None:
                Tag.replace(
                    name=item['translatedName'],
                    slug=item['slug']
                ).execute()

            ProblemTag.replace(
                problem=question['questionId'],
                tag=item['slug']
            ).execute()
        # random_wait(10, 15)

    def fetch_lastSubmission(self,slug):
        query_params = {
                           "operationName":"lastSubmission",
                           "variables":{
                               "lang":"java",
                               "questionSlug":slug
                           },
                           "query":"query lastSubmission($questionSlug: String!, $lang: String!) {\n  lastSubmission(questionSlug: $questionSlug, lang: $lang) {\n    id\n    statusDisplay\n    lang\n    runtime\n    timestamp\n    url\n    isPending\n    memory\n    submissionComment {\n      comment\n      flagType\n      __typename\n    }\n    __typename\n  }\n}\n"
                       }

        resp = self.session.post("https://leetcode.cn/graphql",
                                 data=json.dumps(query_params).encode('utf8'),
                                 headers={
                                     "content-type": "application/json",
                                 })
        body = json.loads(resp.content)

        # parse data
        solutionid = get(body, "data.lastSubmission")['id']
        self.fetch_mySubmissionDetail(solutionid,slug)

    def fetch_mySubmissionDetail(self,solutionid,slug):
        query_params = {
                           "operationName":"mySubmissionDetail",
                           "variables":{
                               "id":solutionid
                           },
                           "query":"query mySubmissionDetail($id: ID!) {\n  submissionDetail(submissionId: $id) {\n    id\n    code\n    runtime\n    memory\n    rawMemory\n    statusDisplay\n    timestamp\n    lang\n    passedTestCaseCnt\n    totalTestCaseCnt\n    sourceUrl\n    question {\n      titleSlug\n      title\n      translatedTitle\n      questionId\n      __typename\n    }\n    ... on GeneralSubmissionNode {\n      outputDetail {\n        codeOutput\n        expectedOutput\n        input\n        compileError\n        runtimeError\n        lastTestcase\n        __typename\n      }\n      __typename\n    }\n    submissionComment {\n      comment\n      flagType\n      __typename\n    }\n    __typename\n  }\n}\n"
                       }

        resp = self.session.post("https://leetcode.cn/graphql",
                                 data=json.dumps(query_params).encode('utf8'),
                                 headers={
                                     "content-type": "application/json",
                                 })
        body = json.loads(resp.content)

        # parse data
        solution = get(body, "data.submissionDetail")
        # Solution.replace(
        #         problem=solution['id'],
        #         url=f"https://leetcode.cn/articles/{slug}/",
        #         content=solution['code']
        #     ).execute()

        Submission.insert(
            id=solution['id'],
            slug=slug,
            language=solution['lang'],
            created=solution['timestamp'],
            source=solution['code']
        ).execute()
        # random_wait(10, 15)

    def fetch_questionSolutionArticles(self, slug):
        print(f"🤖 Fetching solution for problem: {slug}")
        query_params = {
            "operationName":"questionSolutionArticles",
            "variables":{
                "questionSlug":slug,
                "first":10,
                "skip":0,
                "orderBy":"DEFAULT"
            },
            "query":"query questionSolutionArticles($questionSlug: String!, $skip: Int, $first: Int, $orderBy: SolutionArticleOrderBy, $userInput: String, $tagSlugs: [String!]) {\n  questionSolutionArticles(questionSlug: $questionSlug, skip: $skip, first: $first, orderBy: $orderBy, userInput: $userInput, tagSlugs: $tagSlugs) {\n    totalNum\n    edges {\n      node {\n        ...solutionArticle\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment solutionArticle on SolutionArticleNode {\n  rewardEnabled\n  canEditReward\n  uuid\n  title\n  slug\n  sunk\n  chargeType\n  status\n  identifier\n  canEdit\n  canSee\n  reactionType\n  reactionsV2 {\n    count\n    reactionType\n    __typename\n  }\n  tags {\n    name\n    nameTranslated\n    slug\n    tagType\n    __typename\n  }\n  createdAt\n  thumbnail\n  author {\n    username\n    profile {\n      userAvatar\n      userSlug\n      realName\n      __typename\n    }\n    __typename\n  }\n  summary\n  topic {\n    id\n    commentCount\n    viewCount\n    __typename\n  }\n  byLeetcode\n  isMyFavorite\n  isMostPopular\n  isEditorsPick\n  hitCount\n  videosInfo {\n    videoId\n    coverUrl\n    duration\n    __typename\n  }\n  __typename\n}\n"
        }
        resp = self.session.post("https://leetcode.cn/graphql",
                                 data=json.dumps(query_params).encode('utf8'),
                                 headers={
                                     "content-type": "application/json",
                                 })
        body = json.loads(resp.content)

        # parse data
        edges = get(body, "data.questionSolutionArticles.edges")
        if edges != None and len(edges) > 0:
            for edge in edges:
                # if Solution.get_or_none(Solution.problemid == edge['uuid']) is not None:
                #     continue
                if edge!=None and edge["node"]!=None and edge["node"]["byLeetcode"] and edge["node"]["slug"]!=None:
                    return self.fetch_solutionDetailArticle(edge["node"]["slug"])

    def fetch_solutionDetailArticle(self, slug):
        query_params = {
            "operationName":"solutionDetailArticle",
            "variables":{
                "slug":slug,
                "orderBy":"DEFAULT"
            },
            "query":"query solutionDetailArticle($slug: String!, $orderBy: SolutionArticleOrderBy!) {\n  solutionArticle(slug: $slug, orderBy: $orderBy) {\n    ...solutionArticle\n    content\n    question {\n      questionTitleSlug\n      __typename\n    }\n    position\n    next {\n      slug\n      title\n      __typename\n    }\n    prev {\n      slug\n      title\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment solutionArticle on SolutionArticleNode {\n  rewardEnabled\n  canEditReward\n  uuid\n  title\n  slug\n  sunk\n  chargeType\n  status\n  identifier\n  canEdit\n  canSee\n  reactionType\n  reactionsV2 {\n    count\n    reactionType\n    __typename\n  }\n  tags {\n    name\n    nameTranslated\n    slug\n    tagType\n    __typename\n  }\n  createdAt\n  thumbnail\n  author {\n    username\n    profile {\n      userAvatar\n      userSlug\n      realName\n      __typename\n    }\n    __typename\n  }\n  summary\n  topic {\n    id\n    commentCount\n    viewCount\n    __typename\n  }\n  byLeetcode\n  isMyFavorite\n  isMostPopular\n  isEditorsPick\n  hitCount\n  videosInfo {\n    videoId\n    coverUrl\n    duration\n    __typename\n  }\n  __typename\n}\n"
        }

        resp = self.session.post("https://leetcode.cn/graphql",
                                 data=json.dumps(query_params).encode('utf8'),
                                 headers={
                                     "content-type": "application/json",
                                 })
        body = json.loads(resp.content)

        # parse data
        solution = get(body, "data.solutionArticle")
        if solution!=None:
            questionTitleSlug = solution['question']["questionTitleSlug"]
            Solution.replace(
                problem=Problem.get(Problem.slug==questionTitleSlug),
                url=f"https://leetcode.com/articles/{questionTitleSlug}/",
                content=solution['content']
            ).execute()

    def fetch_submission(self, slug):
        print(f"🤖 Fetching submission for problem: {slug}")
        query_params = {
            'operationName': "Submissions",
            'variables': {"offset": 0, "limit": 20, "lastKey": '', "questionSlug": slug},
            'query': '''query Submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!) {
                                        submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug) {
                                        lastKey
                                        hasNext
                                        submissions {
                                            id
                                            statusDisplay
                                            lang
                                            runtime
                                            timestamp
                                            url
                                            isPending
                                            __typename
                                        }
                                        __typename
                                    }
                                }'''
        }

        resp = self.session.post("https://leetcode.cn/graphql",
                                 data=json.dumps(query_params).encode('utf8'),
                                 headers={
                                     "content-type": "application/json",
                                 })
        body = json.loads(resp.content)

        # parse data
        submissions = get(body, "data.submissionList.submissions")
        if len(submissions) > 0:
            for sub in submissions:
                if Submission.get_or_none(Submission.id == sub['id']) is not None:
                    continue

                if sub['statusDisplay'] == 'Accepted':
                    url = sub['url']
                    html = self.session.get(f'https://leetcode.cn{url}').text

                    pattern = re.compile(
                        r'submissionCode: \'(?P<code>.*)\',\n  editCodeUrl', re.S
                    )

                    matched = pattern.search(html)
                    code = matched.groupdict().get('code') if matched else None
                    if code:
                        Submission.insert(
                            id=sub['id'],
                            slug=slug,
                            language=sub['lang'],
                            created=sub['timestamp'],
                            source=code.encode('utf-8')
                        ).execute()
                    else:
                        raise Exception(f"Cannot get submission code for problem: {slug}")
        random_wait(10, 15)


if __name__ == '__main__':
    create_tables()
    crawler = LeetCodeCrawler()
    crawler.login()
    crawler.fetch_accepted_problems()
