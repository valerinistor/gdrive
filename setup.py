from oauth import oauth

if __name__ == '__main__':
    goauth = oauth.GoogleOAuth()
    goauth.authorize()
