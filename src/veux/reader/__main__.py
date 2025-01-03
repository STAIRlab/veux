import veux.reader.csi as csi

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "r") as f:
        tab = csi.load(f)

    csi.create_model(tab, verbose=True)
