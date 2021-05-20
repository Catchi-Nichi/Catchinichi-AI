import mysql_reviews
from scipy.sparse.linalg import svds
import pandas as pd
import numpy as np
import warnings
import argparse

parser = argparse.ArgumentParser(description='Return recommendations from the DB. Return temporary recommendations if it is not yet calculated.')
parser.add_argument('--id', metavar='1', type=str, nargs='+',
                    help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

args = parser.parse_args()


warnings.filterwarnings("ignore")


def get_perfume_data():
    cursor = mysql_reviews.get_cursor()

    reviews_dict = mysql_reviews.get_reviews(cursor)

    user_perfume_data = pd.DataFrame(reviews_dict)

    user_perfume_data["title"] = (
        user_perfume_data["en_name"] + "/" + user_perfume_data["brand"]
    )

    user_perfume_data["rating"] = user_perfume_data["stars"].apply(pd.to_numeric)
    user_perfume_data["userId"] = user_perfume_data["UserNick"]
    nich = user_perfume_data[["userId", "title", "category"]]

    user_perfume_data.drop(
        [
            "id",
            "kr_brand",
            "kr_name",
            "longevity",
            "mood",
            "comment",
            "FragranceBrand",
            "brand",
            "en_name",
            "stars",
            "UserNick",
            "category",
        ],
        axis=1,
        inplace=True,
    )
    return user_perfume_data, nich


def MF_predict(k=20):
    user_perfume_data, nich = get_perfume_data()
    df_user_perfume_rating = user_perfume_data.pivot_table(
        "rating", index="userId", columns="title"
    ).fillna(0)
    user_list = df_user_perfume_rating.index.values
    user_row_dict = dict(zip(list(user_list), range(len(user_list))))
    matrix = df_user_perfume_rating.values
    user_ratings_mean = np.mean(matrix, axis=1)
    matrix_user_mean = matrix - user_ratings_mean.reshape(-1, 1)

    U, sigma, Vt = svds(matrix_user_mean, k=k)
    sigma = np.diag(sigma)
    svd_user_predicted_ratings = np.dot(
        np.dot(U, sigma), Vt
    ) + user_ratings_mean.reshape(-1, 1)
    df_svd_preds = pd.DataFrame(
        svd_user_predicted_ratings, columns=df_user_perfume_rating.columns
    )
    return df_svd_preds, user_row_dict


def recommend_perfumes(user_id, num_recommendations=5):
    user_perfume_data, nich = get_perfume_data()
    df_svd_preds, user_row_dict = MF_predict(20)
    user_row_number = user_row_dict[user_id]
    sorted_user_predictions = df_svd_preds.iloc[user_row_number].sort_values(
        ascending=False
    )
    user_history = user_perfume_data[user_perfume_data.userId == user_id].sort_values(
        ["rating"], ascending=False
    )
    user_perfume_data = user_perfume_data.loc[nich["category"].isin([1])]
    recommendations = user_perfume_data[
        ~user_perfume_data["title"].isin(user_history["title"])
    ]
    recommendations = recommendations.merge(
        pd.DataFrame(sorted_user_predictions).reset_index(), on="title"
    )
    recommendations = recommendations.rename(
        columns={user_row_number: "Predictions"}
    ).sort_values("Predictions", ascending=False)
    recommendations.reset_index(inplace=True)
    recommendations.drop(["userId", "rating", "index"], axis=1, inplace=True)
    recommendations.drop_duplicates(inplace=True)
    recommendations = recommendations.iloc[:num_recommendations, :]
    return recommendations

def main():
    args = sys.argv[]



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Return recommendations from the DB. Return temporary recommendations if it is not yet calculated.')
    parser.add_argument('--id', metavar='1', type=str, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
