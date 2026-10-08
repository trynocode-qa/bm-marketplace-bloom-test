import os

# Test-environment credentials. Environment variables (or .env) can override them, e.g. for another account.
project_owner_credential = {
    'email':os.getenv('BLOOM_PO_EMAIL', 'sawan.hukm+po@bloom.services'),
    'password':os.getenv('BLOOM_PO_PASSWORD', 'Test@1234')
}
