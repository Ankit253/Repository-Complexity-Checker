from flask import Flask, render_template, request, jsonify
import requests
import openai
import json
import base64

app = Flask(__name__)

# Set up OpenAI GPT API credentials
openai.api_key = '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'

# GitHub API endpoint for fetching repositories
GITHUB_API_ENDPOINT = 'https://api.github.com'

# https://github.com/Ankit253?tab=repositories
# Function to fetch repositories for a GitHub user
def fetch_user_repositories(github_url):
    print("--- Find user repo function called---")
    api_url = f"{github_url.rstrip('/')}/repos"
    print(api_url)
    response = requests.get(api_url)
    if response.status_code == 200:
        repositories_data = response.json()
        repositories_urls = [repo_data['html_url'] for repo_data in repositories_data]
        return repositories_urls
    else:
        return []


def fetch_repository_details(repository_url):
    # https://api.github.com/repos/{username}/{repository}
    repository_url = repository_url.replace('github.com', 'api.github.com/repos')
    response = requests.get(repository_url)
    if response.status_code == 200:
        try:
            # print(response.content)  # Print the response content for debugging purposes
            repository_data = json.loads(response.content)
            # print("repository_data: ")
            # print(repository_data)
            repository_details = {
                'name': repository_data['name'],
                'description': repository_data['description'],
                'language': repository_data['language'],
                'url': repository_data['html_url'],
                'readme': fetch_readme(repository_data['html_url'])
            }
            return repository_details
        except (ValueError, KeyError):
            # Error occurred while parsing JSON or extracting repository details
            return None
    else:
        # Response status code is not 200
        return None



# Function to fetch repository's README file
def fetch_readme(contents_url):
    contents_url=contents_url.replace('github.com', 'api.github.com/repos')
    response = requests.get(contents_url.replace('{+path}', 'README.md'))
    if response.status_code == 200:
        readme_data = response.json()
        if readme_data.get('encoding') == 'base64':
            return base64.b64decode(readme_data.get('content')).decode()
    return ''

# Function to evaluate technical complexity using GPT and LangChain
def evaluate_complexity(text):
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=text,
        max_tokens=50,
        temperature=0.3
    )
    complexity = response.choices[0].text
    return complexity

# Function to find the most challenging repository
def find_most_challenging_repository(github_url):
    print("---Started Function 1---")
    repositories_urls = fetch_user_repositories(github_url)
    print("---Fetched user repositories---")
    if not repositories_urls:
        return None

    most_challenging_repo = None
    highest_complexity = 0
    
    print("printing repository URL in function 1")
    print(repositories_urls)

    for repository_url in repositories_urls:
        print("repository_url")
        print(repository_url)
        repository_details = fetch_repository_details(repository_url)
        print("printing repository details: ")
        print(repository_details)
        if repository_details:
            readme_content = repository_details['readme']
            complexity = evaluate_complexity(readme_content)
            print("printing repository complexity: ")
            print(complexity)
            if complexity > highest_complexity:
                highest_complexity = complexity
                most_challenging_repo = repository_details

    return most_challenging_repo

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate_complexity', methods=['POST'])
def calculate_complexity():
    repository_url = request.form['repositoryUrl']

    most_challenging_repository = find_most_challenging_repository(repository_url)
    if most_challenging_repository:
        complexity = most_challenging_repository['complexity']
        # return jsonify({'complexity': complexity})
        return jsonify({'complexity': complexity, 'repository': most_challenging_repository})

    else:
        return jsonify({'error': 'No repositories found or error occurred.'})

if __name__ == '__main__':
    app.run()
