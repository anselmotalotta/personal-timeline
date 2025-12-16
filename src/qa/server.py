# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import os
import sys
import inspect
import os.path as osp
from flask_cors import CORS

from flask import Flask, redirect, url_for, request, render_template, send_from_directory

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# Import QA engines only if langchain is available
try:
    from qa_engine import QAEngine
    from chatgpt_engine import ChatGPTEngine
    # Test if we can actually instantiate them (not just import)
    QA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  QA engines unavailable - missing dependencies: {e}")
    print("   Install langchain, openai, and faiss-cpu to enable Q&A features")
    QA_AVAILABLE = False
    QAEngine = None
    ChatGPTEngine = None
except Exception as e:
    print(f"⚠️  QA engines initialization error: {e}")
    print("   Continuing with degraded functionality")
    QA_AVAILABLE = False
    QAEngine = None
    ChatGPTEngine = None

app = Flask(__name__)
CORS(app)

# # for profiling
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

# Digital data QA engine
qa_engine = None

# ChatGPT Engine (for baseline purpose)
chatgpt_engine = None

@app.route('/test', methods=['GET'])
def test():
    """
    TODO: make calls to the appropriate python function
    TODO: we may want to change these API's to POST apis
    """
    # query = request.args.get('event')
    for key in request.args:
        print(key, request.args[key])
    return {'message': 'okay'}

@app.route('/launch', methods=['GET'])
def launch():
    """Launch a query engine.
    """
    if not QA_AVAILABLE:
        return {'error': 'Q&A features unavailable - missing langchain/openai dependencies'}, 503
    
    global qa_engine
    global chatgpt_engine
    
    try:
        # qa_engine = QAEngine('public/digital_data')
        qa_engine = QAEngine('personal-data/app_data/')
        chatgpt_engine = ChatGPTEngine()
        return {'message': 'okay'}
    except Exception as e:
        return {'error': f'Failed to initialize QA engines: {str(e)}'}, 500


@app.route('/query', methods=['GET'])
def query():
    """Query the posttext engine.
    """
    query = request.args.get('query')
    method = request.args.get('qa')
    print(method)
    
    if not QA_AVAILABLE:
        # Return a basic response instead of error
        return {
            "question": query, 
            "method": method or "basic",
            "answer": f"Q&A features require langchain/openai dependencies. Query was: '{query}'",
            "sources": [],
            "warning": "Install langchain, openai, and faiss-cpu for full Q&A functionality"
        }
    
    if method == 'ChatGPT':
        return {"question": query, "method": method, "answer": chatgpt_engine.query(query), "sources": []}

    # embedding-based QA
    if qa_engine != None:
        res = qa_engine.query(query, method=method)
        res["method"] = method
        return res
    
    # Fallback if qa_engine is None
    return {
        "question": query,
        "method": method or "basic",
        "answer": f"Basic response (Q&A engine not initialized): '{query}'",
        "sources": []
    }


if __name__ == '__main__':
    app.run(host="::", port=8085, debug=True)
