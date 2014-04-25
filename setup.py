from oauth import oauth

if __name__ == '__main__':
    goauth = oauth.GoogleOAuth()
    service = goauth.authorize()
    #goauth.downoadFiles(service)
    goauth.downoadFilesWithFolders(service, 'root', './GoogleDrive')
