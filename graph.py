"""Graph visualization utility using langchain_teddynote.graphs."""

from pathlib import Path

from langchain_teddynote.graphs import NodeStyles, visualize_graph

from app import build_graph


def main() -> None:
    compiled = build_graph().compile()

    # Display in notebook/terminal (depending on environment)
    visualize_graph(compiled)

    # Save PNG snapshot for documentation
    output_path = Path("outputs/edge_ai_graph.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    png_bytes = compiled.get_graph().draw_mermaid_png(
        background_color="white",
        node_colors=NodeStyles(),
    )
    output_path.write_bytes(png_bytes)
    print(f"그래프 이미지를 저장했습니다: {output_path.resolve()}")


if __name__ == "__main__":
    main()
