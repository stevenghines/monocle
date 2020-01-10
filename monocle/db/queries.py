# MIT License
# Copyright (c) 2019 Fabien Boucher

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def generate_filter(
        repository_fullname, gte=None, lte=None, etype=None, state=None):
    created_at_range = {
        "created_at": {
            "format": "epoch_millis"
        }
    }
    if gte:
        created_at_range['created_at']['gte'] = gte
    if lte:
        created_at_range['created_at']['lte'] = lte
    qfilter = [
        {"regexp": {
            "repository_fullname": {
                "value": repository_fullname}}},
        {"range": created_at_range}
    ]
    if etype:
        qfilter.append({"term": {"type": etype}})
    if state:
        qfilter.append({"term": {"state": state}})
    return qfilter


def run_query(es, index, body):
    params = {'index': index, 'doc_type': index}
    params['body'] = body
    try:
        res = es.search(**params)
    except Exception:
        return (0, 0, [])
    took = res['took']
    hits = res['hits']['total']
    return took, hits, res


def events_histo(
        es, index,
        repository_fullname, gte, lte, etype, interval="30m"):
    body = {
        "aggs": {
            "agg1": {
                "date_histogram": {
                    "field": "created_at",
                    "interval": interval,
                }
            }
        },
        "size": 0,
        "query": {
            "bool": {
                "filter": generate_filter(
                    repository_fullname, gte, lte, etype),
                "should": [],
                "must_not": []
            }
        }
    }
    took, hits, data = run_query(es, index, body)
    return took, hits, data['aggregations']['agg1']['buckets']


def _events_top(
        es, index, field,
        repository_fullname, gte, lte, etype, interval=None, size=10):
    body = {
        "aggs": {
            "agg1": {
                "terms": {
                    "field": field,
                    "size": size,
                    "order": {
                        "_count": "desc"
                    }
                }
            }
        },
        "size": 0,
        "query": {
            "bool": {
                "filter": generate_filter(
                    repository_fullname, gte, lte, etype),
                "should": [],
                "must_not": []
            }
        }
    }
    took, hits, data = run_query(es, index, body)
    return took, hits, data['aggregations']['agg1']['buckets']


def events_top_authors(
        es, index,
        repository_fullname, gte, lte, etype, interval=None, size=10):
    return _events_top(
        es, index, "author", repository_fullname,
        gte, lte, etype, interval, size)


def events_top_approval(
        es, index,
        repository_fullname, gte, lte, etype, interval=None, size=10):
    return _events_top(
        es, index, "approval", repository_fullname,
        gte, lte, etype, interval, size)


def change_merged_count_by_duration(
        es, index,
        repository_fullname, gte, lte, etype, interval=None, size=None):
    body = {
        "aggs": {
            "agg1": {
                "range": {
                    "field": "duration",
                    "ranges": [
                        {
                            "to": 24*3600
                        },
                        {
                            "from": 24*3600+1,
                            "to": 7*24*3600
                        },
                        {
                            "from": 7*24*3600+1,
                            "to": 31*24*3600
                        },
                        {
                            "from": 31*24*3600+1
                        },
                    ],
                    "keyed": True
                }
            }
        },
        "size": 0,
        "query": {
            "bool": {
                "filter": generate_filter(
                    repository_fullname, gte, lte, "Change", "MERGED"),
                "should": [],
                "must_not": []
            }
        }
    }
    took, hits, data = run_query(es, index, body)
    return took, hits, data['aggregations']['agg1']['buckets']


def pr_merged_avg_duration(
        es, index,
        repository_fullname, gte, lte, etype, interval=None, size=None):
    body = {
        "aggs": {
            "agg1": {
                "avg": {
                    "field": "duration"
                }
            }
        },
        "size": 0,
        "docvalue_fields": [
            {
                "field": "created_at",
                "format": "date_time"
            },
        ],
        "query": {
            "bool": {
                "filter": generate_filter(
                    repository_fullname, gte, lte, "PullRequest", "MERGED"),
                "should": [],
                "must_not": []
            }
        }
    }
    took, hits, data = run_query(es, index, body)
    return took, hits, data['aggregations']['agg1']