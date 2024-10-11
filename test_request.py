import requests

def test_url(url):
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type')}")
        print(f"Content (first 200 characters): {response.text[:200]}")
    except requests.exceptions.SSLError as e:
        print(f"SSL Error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Test both URLs
test_url("https://eprint.iacr.org/rss/rss.xml?order=recent")
print("\n---\n")
test_url("https://rss.arxiv.org/rss/cs.CR")