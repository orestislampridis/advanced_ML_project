import pandas as pd
import numpy as np
from costcla.sampling import cost_sampling
from sklearn.ensemble import RandomForestClassifier


class Cost:
    # classes => 1 = Recession, 0 = No_Recession
    recession = 1
    growth = 0

    cost_recession_predicted_recession = 0
    cost_recession_predicted_growth = 0
    cost_growth_predicted_recession = 0
    cost_growth_predicted_growth = 0

    def __init__(self, cost_recession_predicted_growth: int, cost_growth_predicted_recession: int,
                 cost_recession_predicted_recession: int = 0, cost_growth_predicted_growth: int = 0):
        self.cost_recession_predicted_recession = cost_recession_predicted_recession
        self.cost_recession_predicted_growth = cost_recession_predicted_growth
        self.cost_growth_predicted_recession = cost_growth_predicted_recession
        self.cost_growth_predicted_growth = cost_growth_predicted_growth

    def cost_matrix(self):
        return [
            [self.cost_growth_predicted_growth, self.cost_recession_predicted_growth],
            [self.cost_growth_predicted_recession, self.cost_recession_predicted_recession]
        ]

    def costcla_cost_array(self, label):
        cost_matrix = self.cost_matrix()
        # Flatten & Reshape cost matrix for specific class

        flat_cost_matrix = []
        #  Do NOT use this!!! Use the plain cost matrix - seems to give proper results (although biased)
        #  costcla = > [false positives, false negatives, true positives, true negatives]
        if label == self.recession:
            flat_cost_matrix = [self.cost_growth_predicted_recession,
                                self.cost_recession_predicted_growth,
                                self.cost_recession_predicted_recession,
                                self.cost_growth_predicted_growth]
        elif label == self.growth:
            flat_cost_matrix = [self.cost_recession_predicted_growth,
                                self.cost_growth_predicted_recession,
                                self.cost_growth_predicted_growth,
                                self.cost_recession_predicted_recession]

        return np.asarray(cost_matrix).flatten()

    def cost_growth(self):
        cost = 0

        for row in self.cost_matrix():
            growth_cost = row[0]
            cost += growth_cost

        return cost

    def cost_recession(self):
        cost = 0

        for row in self.cost_matrix():
            recession_cost = row[1]
            cost += recession_cost

        return cost

    def recession_weight(self, x, y):
        n = 0
        n_recession = 0
        n_growth = 0

        for example_y in y:
            if example_y == self.growth:
                n_growth += 1
            elif example_y == self.recession:
                n_recession += 1
            else:
                raise AssertionError("More than 2 classes found in dataset.")

            n += 1

        cost_recession = self.cost_recession()
        cost_growth = self.cost_growth()

        return n * cost_recession / ((n_growth * cost_growth) + (n_recession * cost_recession))

    def growth_weight(self, dataset: pd.DataFrame):
        n = 0
        n_recession = 0
        n_growth = 0

        for row in dataset.values:
            example_class = row[-1]

            if example_class == self.growth:
                n_growth += 1
            elif example_class == self.recession:
                n_recession += 1
            else:
                raise AssertionError("More than 2 classes found in dataset.")

            n += 1

        cost_recession = self.cost_recession()
        cost_growth = self.cost_growth()

        return n * cost_growth / ((n_growth * cost_growth) + (n_recession * cost_recession))


def cost_sensitive_data_re_balance(x, y, cost: Cost, method="RejectionSampling", norm=0.1, wc=97.5):
    """

    :param x: the examples in the dataset expect an array of shape [n,f] of n samples with f features
    :param y: the label of each sample in the same order
    :param cost: the cost definition
    :return: [x], [y], cost_mat_cps
    """
    # print("----Rejection Sampling----")
    costs = []

    for current_y in y:
        costs_array = cost.costcla_cost_array(current_y)
        costs.append(costs_array)

    costs = np.asarray(costs)

    x, y, c = cost_sampling(x, y, costs, method=method, oversampling_norm=norm, max_wc=wc)
    return x, y


#   http://albahnsen.github.io/CostSensitiveClassification/Models.html

def cost_grid_search(method="RejectionSampling", norm=0.1, wc=97.5):
    data = pd.read_csv("./dataset/africa_recession.csv", delimiter=",")

    x = np.asarray(data.iloc[:, :-1])
    y = np.asarray(data.iloc[:, -1])

    cost_recession_predicted_growth = 0.1
    cost_growth_predicted_recession = 0.1

    for n_recession_p_growth in range(0, 100):
        for n_growth_p_recession in range(0, 100):
            cost_recession_predicted_growth = 0.1 * n_recession_p_growth
            cost_growth_predicted_recession = 0.1 * n_growth_p_recession

            cost = Cost(cost_recession_predicted_growth, cost_growth_predicted_recession)

            new_x, new_y = cost_sensitive_data_re_balance(x, y, cost, method, norm, wc)

            recession_count = 0
            growth_count = 0

            for current_y in new_y:
                if current_y == 1:
                    recession_count += 1
                else:
                    recession_count += 1

            if growth_count == 0:
                continue

            print("Params:", method, norm, wc)
            print("Costs (", cost_recession_predicted_growth, ",", cost_growth_predicted_recession, ") => Counts ("
                  "Recession:", recession_count, "Growth:", growth_count, ").")


def cost_sensitive_sampling_grid_search():
    oversampling = "OverSampling"
    rejection_sampling = "RejectionSampling"

    for n in range(0, 100):
        norm = float(n)/100

        for n_wc in range(0, 100):
            wc = float(n_wc)

            for method in [rejection_sampling, oversampling]:
                cost_grid_search(method, norm, wc)

if __name__ == '__main__':
    cost_sensitive_sampling_grid_search()
