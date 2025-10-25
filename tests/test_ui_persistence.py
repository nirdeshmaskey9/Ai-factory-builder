def test_local_storage_js_present():
  data = open('ai_factory/ui/static/js/ui_helpers.js','r',encoding='utf-8').read()
  assert 'localStorage' in data or 'toast' in data

