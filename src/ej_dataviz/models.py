from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _
import pandas as pd

from ej_conversations.models import Conversation

from .utils import (
    add_group_column,
    get_cluster_or_404,
    get_clusters,
    get_comments_dataframe,
)


class CommentsReportClustersFilter:
    def __init__(self, cluster_ids: list, conversation: Conversation):
        self.cluster_ids = cluster_ids
        self.conversation = conversation
        self.clusters_filters = []

    def filter(self):
        comments_df = get_comments_dataframe(self.conversation.comments, "")
        if not self.cluster_ids:
            return comments_df
        for cluster_id in self.cluster_ids:
            try:
                cluster = get_cluster_or_404(cluster_id, self.conversation)
                self.clusters_filters.append(cluster.name)
            except Exception:
                pass
        clusters = get_clusters(self.conversation)
        commentsDataframeUtils = CommentsDataframeUtils(comments_df)
        return commentsDataframeUtils.filter_by_cluster(clusters, self.clusters_filters)


class CommentsReportSearchFilter:
    def __init__(self, text: str, comments: list, comments_df: pd.DataFrame):
        self.text = text
        self.comments = comments
        self.comments_df = comments_df

    def filter(self):
        commentsDataframeUtils = CommentsDataframeUtils(self.comments_df)
        if self.text:
            return commentsDataframeUtils.search_content(self.text)
        return self.comments_df


class CommentsReportOrderByFilter:
    def __init__(self, order, comments, comments_df: pd.DataFrame, ascending=False):
        self.comments = comments
        self.order = order
        self.ascending = ascending
        self.comments_df = comments_df

    def filter(self):
        if not self.order or self.order == "created":
            return self.comments_df.sort_values("comment", ascending=self.ascending)
        return self.comments_df.sort_values(self.order, ascending=self.ascending)


class ToolsLinksHelper:
    """
    Implements the business rule that decides which bot will
    be used.
    """

    AVAILABLE_ENVIRONMENT_MAPPING = {
        "http://localhost:8000": "https://t.me/DudaLocalBot?start=",
        "https://ejplatform.pencillabs.com.br": "https://t.me/DudaEjDevBot?start=",
        "https://www.ejplatform.org": "https://t.me/DudaEjBot?start=",
    }

    @staticmethod
    def get_bot_link(host):
        return (
            ToolsLinksHelper.AVAILABLE_ENVIRONMENT_MAPPING.get(host)
            or "https://t.me/DudaLocalBot?start="
        )


@dataclass
class CommentsDataframeUtils:

    comments_df: pd.DataFrame

    def search_content(self, text):
        """
        Filter the comments dataframe by the content column. It will be checked if the
        content has the substring variable.
        """
        return self.comments_df[self.comments_df.content.str.contains(text, case=False)]

    def get_cluster_comments_df(self, cluster, cluster_name):
        """
        Gets the cluster comments dataframe from comments_statistics_summary_dataframe
        and sets the group column for each comment row.
        """
        df = cluster.comments_statistics_summary_dataframe(normalization=100)
        add_group_column(df, cluster_name)
        return df

    def filter_by_cluster(self, clusters, cluster_filters):
        """
        Gets the conversation comments (comments_df) and cluster comments
        filtered by the group specified in cluster_filters.
        """
        for cluster in clusters:
            if cluster.name in cluster_filters:
                cluster_comments_df = self.get_cluster_comments_df(cluster, cluster.name)
                self.comments_df = self.comments_df.append(cluster_comments_df)

        if "general" not in cluster_filters:
            self.comments_df = self.comments_df[self.comments_df.group != ""]

        return self.comments_df
