from mounts_project import MountsProject


def main():
    mounts = MountsProject(verbose=True)

    # Extract only
    mounts.extract()

    # Get results
    data = mounts.data

    # Save to excel to CSV
    mounts.save(filetype="xlsx")


if __name__ == "__main__":
    main()
