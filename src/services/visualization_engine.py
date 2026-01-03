"""
Visualization Engine

Automated generation of high-quality visualizations for EDA.
Supports multiple chart types with intelligent chart selection.
"""

import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

matplotlib.use("Agg")  # Non-interactive backend for server environments

from src.core.config import settings
from src.core.exceptions import VisualizationException
from src.core.logging import get_logger
from src.models.schemas import DataType, Visualization

logger = get_logger(__name__)


class VisualizationEngine:
    """
    Generates comprehensive visualizations for exploratory data analysis
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.file_upload.results_dir
        self.dpi = settings.visualization.plot_dpi
        self.format = settings.visualization.plot_format
        self.figsize = (
            settings.visualization.figure_size_width,
            settings.visualization.figure_size_height,
        )
        self.color_palette = settings.visualization.color_palette
        self.max_plots = settings.visualization.max_plots

        # Set style
        sns.set_style("whitegrid")
        sns.set_palette(self.color_palette)

    def generate_all_visualizations(
        self, df: pd.DataFrame, column_types: dict, job_id: str
    ) -> List[Visualization]:
        """
        Generate all relevant visualizations for the dataset

        Args:
            df: DataFrame to visualize
            column_types: Dictionary mapping column names to DataType
            job_id: Job identifier for file naming

        Returns:
            List of Visualization objects
        """
        logger.info(f"Generating visualizations for job {job_id}")

        visualizations = []
        plot_count = 0

        try:
            # Numeric distributions
            numeric_columns = [
                col for col, dtype in column_types.items() if dtype == DataType.NUMERIC
            ]

            for column in numeric_columns[:min(10, len(numeric_columns))]:
                if plot_count >= self.max_plots:
                    break

                # Histogram
                viz = self.create_histogram(df, column, job_id)
                if viz:
                    visualizations.append(viz)
                    plot_count += 1

                # Box plot
                if plot_count < self.max_plots:
                    viz = self.create_boxplot(df, column, job_id)
                    if viz:
                        visualizations.append(viz)
                        plot_count += 1

            # Correlation heatmap
            if len(numeric_columns) >= 2 and plot_count < self.max_plots:
                viz = self.create_correlation_heatmap(df, numeric_columns, job_id)
                if viz:
                    visualizations.append(viz)
                    plot_count += 1

            # Categorical distributions
            categorical_columns = [
                col
                for col, dtype in column_types.items()
                if dtype == DataType.CATEGORICAL
            ]

            for column in categorical_columns[:min(5, len(categorical_columns))]:
                if plot_count >= self.max_plots:
                    break

                viz = self.create_bar_chart(df, column, job_id)
                if viz:
                    visualizations.append(viz)
                    plot_count += 1

            # Pairwise relationships (for top numeric columns)
            if len(numeric_columns) >= 2 and plot_count < self.max_plots:
                top_columns = numeric_columns[:min(4, len(numeric_columns))]
                viz = self.create_pairplot(df, top_columns, job_id)
                if viz:
                    visualizations.append(viz)
                    plot_count += 1

            logger.info(f"Generated {len(visualizations)} visualizations")

            return visualizations

        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}", exc_info=True)
            raise VisualizationException(f"Failed to generate visualizations: {str(e)}")

    def create_histogram(
        self, df: pd.DataFrame, column: str, job_id: str
    ) -> Optional[Visualization]:
        """
        Create histogram for numeric column

        Args:
            df: DataFrame containing the column
            column: Column name to visualize
            job_id: Job identifier

        Returns:
            Visualization object or None if failed
        """
        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            data = df[column].dropna()

            # Create histogram with KDE
            ax.hist(data, bins="auto", alpha=0.7, edgecolor="black", density=True)

            # Add KDE if enough data points
            if len(data) > 10:
                from scipy import stats

                kde = stats.gaussian_kde(data)
                x_range = np.linspace(data.min(), data.max(), 100)
                ax.plot(x_range, kde(x_range), "r-", linewidth=2, label="KDE")
                ax.legend()

            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel("Density", fontsize=12)
            ax.set_title(f"Distribution of {column}", fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_histogram_{column}.{self.format}"
            filepath = self.output_dir / filename

            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)

            return Visualization(
                viz_id=viz_id,
                viz_type="histogram",
                title=f"Distribution of {column}",
                file_path=str(filepath),
                columns_used=[column],
                description=f"Histogram showing the distribution of values in {column}",
            )

        except Exception as e:
            logger.warning(f"Failed to create histogram for {column}: {str(e)}")
            plt.close("all")
            return None

    def create_boxplot(
        self, df: pd.DataFrame, column: str, job_id: str
    ) -> Optional[Visualization]:
        """
        Create box plot for numeric column

        Args:
            df: DataFrame containing the column
            column: Column name to visualize
            job_id: Job identifier

        Returns:
            Visualization object or None if failed
        """
        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            data = df[column].dropna()

            # Create box plot
            bp = ax.boxplot(
                data,
                vert=True,
                patch_artist=True,
                notch=True,
                showmeans=True,
                meanprops=dict(marker="D", markerfacecolor="red", markersize=8),
            )

            # Customize colors
            for patch in bp["boxes"]:
                patch.set_facecolor("lightblue")
                patch.set_alpha(0.7)

            ax.set_ylabel(column, fontsize=12)
            ax.set_title(
                f"Box Plot of {column}", fontsize=14, fontweight="bold"
            )
            ax.grid(True, alpha=0.3, axis="y")

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_boxplot_{column}.{self.format}"
            filepath = self.output_dir / filename

            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)

            return Visualization(
                viz_id=viz_id,
                viz_type="boxplot",
                title=f"Box Plot of {column}",
                file_path=str(filepath),
                columns_used=[column],
                description=f"Box plot showing the distribution, quartiles, and outliers in {column}",
            )

        except Exception as e:
            logger.warning(f"Failed to create boxplot for {column}: {str(e)}")
            plt.close("all")
            return None

    def create_correlation_heatmap(
        self, df: pd.DataFrame, columns: List[str], job_id: str
    ) -> Optional[Visualization]:
        """
        Create correlation heatmap for numeric columns

        Args:
            df: DataFrame containing the columns
            columns: List of column names to include
            job_id: Job identifier

        Returns:
            Visualization object or None if failed
        """
        try:
            # Calculate correlation matrix
            corr_matrix = df[columns].corr()

            # Create figure
            fig, ax = plt.subplots(
                figsize=(max(10, len(columns)), max(8, len(columns) * 0.8))
            )

            # Create heatmap
            sns.heatmap(
                corr_matrix,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                center=0,
                square=True,
                linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )

            ax.set_title(
                "Correlation Heatmap", fontsize=14, fontweight="bold"
            )

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_correlation_heatmap.{self.format}"
            filepath = self.output_dir / filename

            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)

            return Visualization(
                viz_id=viz_id,
                viz_type="heatmap",
                title="Correlation Heatmap",
                file_path=str(filepath),
                columns_used=columns,
                description="Heatmap showing correlations between numeric variables",
            )

        except Exception as e:
            logger.warning(f"Failed to create correlation heatmap: {str(e)}")
            plt.close("all")
            return None

    def create_bar_chart(
        self, df: pd.DataFrame, column: str, job_id: str, top_n: int = 15
    ) -> Optional[Visualization]:
        """
        Create bar chart for categorical column

        Args:
            df: DataFrame containing the column
            column: Column name to visualize
            job_id: Job identifier
            top_n: Number of top categories to show

        Returns:
            Visualization object or None if failed
        """
        try:
            # Get value counts
            value_counts = df[column].value_counts().head(top_n)

            fig, ax = plt.subplots(figsize=self.figsize)

            # Create bar chart
            value_counts.plot(kind="bar", ax=ax, color="steelblue", alpha=0.8)

            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel("Count", fontsize=12)
            ax.set_title(
                f"Top {len(value_counts)} Categories in {column}",
                fontsize=14,
                fontweight="bold",
            )
            ax.grid(True, alpha=0.3, axis="y")

            # Rotate labels if needed
            if max([len(str(label)) for label in value_counts.index]) > 10:
                plt.xticks(rotation=45, ha="right")

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_barchart_{column}.{self.format}"
            filepath = self.output_dir / filename

            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)

            return Visualization(
                viz_id=viz_id,
                viz_type="bar_chart",
                title=f"Distribution of {column}",
                file_path=str(filepath),
                columns_used=[column],
                description=f"Bar chart showing frequency distribution of categories in {column}",
            )

        except Exception as e:
            logger.warning(f"Failed to create bar chart for {column}: {str(e)}")
            plt.close("all")
            return None

    def create_pairplot(
        self, df: pd.DataFrame, columns: List[str], job_id: str
    ) -> Optional[Visualization]:
        """
        Create pairwise scatter plot matrix

        Args:
            df: DataFrame containing the columns
            columns: List of column names to include
            job_id: Job identifier

        Returns:
            Visualization object or None if failed
        """
        try:
            # Sample data if too large
            sample_df = df[columns].dropna()
            if len(sample_df) > 1000:
                sample_df = sample_df.sample(1000, random_state=42)

            # Create pairplot
            g = sns.pairplot(
                sample_df,
                diag_kind="kde",
                plot_kws={"alpha": 0.6, "s": 30},
                diag_kws={"alpha": 0.7},
            )

            g.fig.suptitle(
                "Pairwise Relationships", y=1.01, fontsize=14, fontweight="bold"
            )

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_pairplot.{self.format}"
            filepath = self.output_dir / filename

            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
            plt.close(g.fig)

            return Visualization(
                viz_id=viz_id,
                viz_type="pairplot",
                title="Pairwise Relationships",
                file_path=str(filepath),
                columns_used=columns,
                description="Pairwise scatter plots showing relationships between numeric variables",
            )

        except Exception as e:
            logger.warning(f"Failed to create pairplot: {str(e)}")
            plt.close("all")
            return None

    def create_interactive_scatter(
        self, df: pd.DataFrame, x_col: str, y_col: str, job_id: str, color_col: Optional[str] = None
    ) -> Optional[Visualization]:
        """
        Create interactive scatter plot using Plotly

        Args:
            df: DataFrame containing the columns
            x_col: X-axis column name
            y_col: Y-axis column name
            job_id: Job identifier
            color_col: Optional column for color encoding

        Returns:
            Visualization object or None if failed
        """
        try:
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col} vs {x_col}",
                labels={x_col: x_col, y_col: y_col},
                template="plotly_white",
            )

            fig.update_traces(marker=dict(size=8, opacity=0.7))

            # Save plot
            viz_id = str(uuid.uuid4())
            filename = f"{job_id}_{viz_id}_scatter_{x_col}_{y_col}.html"
            filepath = self.output_dir / filename

            fig.write_html(str(filepath))

            columns_used = [x_col, y_col]
            if color_col:
                columns_used.append(color_col)

            return Visualization(
                viz_id=viz_id,
                viz_type="scatter_plot",
                title=f"{y_col} vs {x_col}",
                file_path=str(filepath),
                columns_used=columns_used,
                description=f"Interactive scatter plot of {y_col} against {x_col}",
            )

        except Exception as e:
            logger.warning(f"Failed to create scatter plot: {str(e)}")
            return None

    def cleanup_old_visualizations(self, age_days: int = 7) -> None:
        """
        Clean up old visualization files

        Args:
            age_days: Remove files older than this many days
        """
        try:
            import time
            from datetime import datetime, timedelta

            cutoff_time = time.time() - (age_days * 86400)

            removed_count = 0
            for file_path in self.output_dir.glob(f"*.{self.format}"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed_count += 1

            if removed_count > 0:
                logger.info(
                    f"Cleaned up {removed_count} old visualization files"
                )

        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")
