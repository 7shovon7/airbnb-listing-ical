import firebase_admin
from firebase_admin import credentials, firestore, storage


def initialize_firebase(creds_path, storage_bucket):
    cred = credentials.Certificate(creds_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': storage_bucket
    })


# creds_path = '/Users/mars/Downloads/general-ad3e9-firebase-adminsdk-ejz1e-db056b4f3e.json'
# cred = credentials.Certificate(creds_path)
# firebase_admin.initialize_app(cred, {
#     'storageBucket': 'general-ad3e9.appspot.com'
# })

def upload_ical_file(ical_content, listing_id):
    bucket = storage.bucket()
    blob = bucket.blob(f"{listing_id}.ics")
    blob.upload_from_string(ical_content, content_type='text/calendar')
    download_url = blob.public_url
    return download_url


def store_ical_link(listing_id, ical_link, download_url):
    db = firestore.client()
    doc_ref = db.collection('listings').document(listing_id)
    doc_ref.set({
        'ical_link': ical_link,
        'storage_url': download_url,
        'last_updated': firestore.SERVER_TIMESTAMP
    })
    
    
def update_ical_link(listing_id, ical_link, download_url):
    db = firestore.client()
    doc_ref = db.collection('listings').document(listing_id)
    doc_ref.update({
        'ical_link': ical_link,
        'storage_url': download_url,
        'last_updated': firestore.SERVER_TIMESTAMP
    })
