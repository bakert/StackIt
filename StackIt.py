import os, sys

if __name__ == "__main__":
    if (len(sys.argv) == 1):
        import GUIapp
        GUIapp.main()
    else:
        if os.path.isdir(sys.argv[1]):
            import watcher
            watcher.main(sys.argv[1])
        else:
            import builder
            builder.main(sys.argv[1])
