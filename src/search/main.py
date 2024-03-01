import os
from argparse import ArgumentParser, Namespace

from dotenv import load_dotenv
from utilities import AISearchClient


def main(args: Namespace) -> None:
    # Create search client
    search_client = AISearchClient(
        search_endpoint=os.environ["AZURE_AI_SEARCH_ENDPOINT"],
        api_key=os.environ["AZURE_AI_SEARCH_KEY"],
    )

    # Generate list of variables to be used in templates
    template_variables = {
        key: value for key, value in os.environ.items() if key.startswith(("AZURE"))
    }

    # Load data source template
    data_source_template_path = os.path.join(
        args.search_templates_dir, "data-source.json"
    )
    search_client.load_data_source_template(
        data_source_name=os.environ["AZURE_AI_SEARCH_DATASOURCE_NAME"],
        data_source_template_path=data_source_template_path,
        template_variables=template_variables,
    )

    # Load index template
    index_template_path = os.path.join(args.search_templates_dir, "index.json")
    search_client.load_index_template(
        index_name=os.environ["AZURE_AI_SEARCH_INDEX_NAME"],
        index_template_path=index_template_path,
        template_variables=template_variables,
    )

    # Load skillset template
    skillset_template_path = os.path.join(args.search_templates_dir, "skillset.json")
    search_client.load_skillset_template(
        skillset_name=os.environ["AZURE_AI_SEARCH_SKILLSET_NAME"],
        skillset_template_path=skillset_template_path,
        template_variables=template_variables,
    )

    # Load indexer template
    indexer_template_path = os.path.join(args.search_templates_dir, "indexer.json")
    search_client.load_indexer_template(
        indexer_name=os.environ["AZURE_AI_SEARCH_INDEXER_NAME"],
        indexer_template_path=indexer_template_path,
        template_variables=template_variables,
    )

    # Create the data source
    response = search_client.create_data_source()
    print(
        "Create the data source...\n",
        f"Status: {response.status_code}\n",
        f"Response text: {response.text}\n",
    )

    # Create the index
    response = search_client.create_index()
    print(
        "Create the index...\n",
        f"Status: {response.status_code}\n",
        f"Response text: {response.text}\n",
    )

    # Create skillset to enhance the indexer
    response = search_client.create_skillset()
    print(
        "Create skillset to enhance the indexer...\n",
        f"Status: {response.status_code}\n",
        f"Response text: {response.text}\n",
    )

    # Create the indexer
    response = search_client.create_indexer()
    print(
        "Create the indexer...\n",
        f"Status: {response.status_code}\n",
        f"Response text: {response.text}\n",
    )


def parse_args() -> Namespace:
    """Parse command line arguments"""
    # setup arg parser
    parser = ArgumentParser()

    # add arguments
    parser.add_argument("--search_templates_dir", type=str)

    # parse args
    args = parser.parse_args()
    print(args)

    return args


if __name__ == "__main__":
    load_dotenv()
    main(parse_args())
