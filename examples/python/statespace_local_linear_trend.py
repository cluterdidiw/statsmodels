# coding: utf-8

# DO NOT EDIT
# Autogenerated from the notebook statespace_local_linear_trend.ipynb.
# Edit the notebook and then sync the output with this file.
#
# flake8: noqa
# DO NOT EDIT

# # 状态空间建模：局部线性趋势

# 这个笔记描述了如何扩展 statsmodels 状态空间类以创建和估计自定义模型。在这里，我们开发了一个局部线性趋势模型。
#
# 局部线性趋势模型具有以下形式（有关注释和详细信息，请参见 Durbin 和 Koopman 2012，第3.2章）：
#
# $$
# \begin{align}
# y_t & = \mu_t + \varepsilon_t \qquad & \varepsilon_t \sim
#     N(0, \sigma_\varepsilon^2) \\
# \mu_{t+1} & = \mu_t + \nu_t + \xi_t & \xi_t \sim N(0, \sigma_\xi^2) \\
# \nu_{t+1} & = \nu_t + \zeta_t & \zeta_t \sim N(0, \sigma_\zeta^2)
# \end{align}
# $$
#
# 很容易看出，可以将其转换为状态空间形式：
#
# $$
# \begin{align}
# y_t & = \begin{pmatrix} 1 & 0 \end{pmatrix} \begin{pmatrix} \mu_t \\
# \nu_t \end{pmatrix} + \varepsilon_t \\
# \begin{pmatrix} \mu_{t+1} \\ \nu_{t+1} \end{pmatrix} & = \begin{bmatrix}
# 1 & 1 \\ 0 & 1 \end{bmatrix} \begin{pmatrix} \mu_t \\ \nu_t \end{pmatrix}
# + \begin{pmatrix} \xi_t \\ \zeta_t \end{pmatrix}
# \end{align}
# $$
#
# 注意，许多状态空间画像是由已知值组成的。 实际上，要估计参数的唯一部分出现在方差/协方差矩阵中：
#
# $$
# \begin{align}
# H_t & = \begin{bmatrix} \sigma_\varepsilon^2 \end{bmatrix} \\
# Q_t & = \begin{bmatrix} \sigma_\xi^2 & 0 \\ 0 & \sigma_\zeta^2
# \end{bmatrix}
# \end{align}
# $$

import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
import matplotlib.pyplot as plt

# 为了利用包括卡尔曼滤波和最大似然估计在内的现有基础架构，我们创建了一个新的类，该类继承了 
# `statsmodels.tsa.statespace.MLEModel` 类。必须指定许多内容：
# 
#
# 1. ** k_states **，** k_posdef **：这两个参数必须在初始化时提供给基类​​。状态空间模型分别报告了在$\begin{pmatrix} \mu_t & \nu_t \end{pmatrix}'$ ，
# 之上的状态向量和在 $\begin{pmatrix} \xi_t & \zeta_t \end{pmatrix}'$ 状态误差向量的大小。注意，不必指定内生向量的维数，因为它可以从 `endog` 数组中推断出来
#
# 2. ** update **：`update` 方法带有必须指定的 `params` 参数（通常调用 `fit()` 方法来计算 MLE ）。它采用参数并将其填充到适当的状态空间矩阵中。
# 例如，下面的 `params` 向量包含方差参数$\begin{pmatrix} \sigma_\varepsilon^2 & \sigma_\xi^2 & \sigma_\zeta^2\end{pmatrix}$，以及`update`方法
# 必须将它们放入观测和状态协方差矩阵中。一般来说，参数向量可以映射到所有状态空间矩阵中的许多不同位置。
#
# 3. **statespace matrices**：默认情况下，所有状态空间矩阵（obs_intercept，design，obs_cov，state_intercept，transition，selection，state_cov）均设置为零。
# 可以在初始化时设置固定的值（如此处的设计矩阵和过渡矩阵的值），而随参数而变化的值应在 `update` 方法中设置。请注意，很容易忘记设置 selection 矩阵，
# 该矩阵通常只是单位矩阵（如此处所示），但是如果不设置它，则会导致模型非常不同（一个没有随机成分的过渡方程）。
#
# 4. **start params**：start parameters 必须设置，尽管 start parameters 可以从数据中找到良好的初始参数，即使只是零的向量，也必须设置初始参数。通过梯度方法（此处采用）
# 进行的极大似然估计可能对初始参数敏感，因此，如果可能的话，选择良好的参数非常重要。此处并没有太大关系（尽管作为方差，不应将其设置为零）
#
# **initialization**：除了定义的状态空间矩阵之外，所有状态空间模型还必须使用均值和方差来初始化，用于状态向量的初始分布。 
# 如果已知分布，则可以调用 `initialize_known(initial_state, initial_state_cov)`，或者如果模型是固定的（例如ARMA模型），
# 则可以使用 `initialize_stationary`。 否则，`initialize_approximate_diffuse` 是一个合理通用的初始化（明确扩散的初始化尚不可用）。
# 由于局部线性趋势模型不是固定的（它由随机游走组成），并且由于分布通常是未知的，因此我们在下面使用 `initialize_approximate_diffuse`。
#
# 以上设置是成功建模的最低要求。 还有许多设置不是必须设置的，但对于某些应用程序可能有帮助或重要：
#
# 1.**transform / untransform**:：当调用`fit`时，后台的优化器将使用梯度方法来选择使似然函数最大化的参数。 默认情况下，它使用无界优化，
# 这意味着它可以选择任何参数值。 在许多情况下，这不是理想的行为，例如，方差不能为负。 为了解决这个问题，`transform` 方法采用了优化器提供
# 参数的无约束向量，并返回一个在似然评估中使用参数的约束向量。 `untransform` 提供相反的操作。
#
# 2.**param_names**：这个内置方法可用于设置估算参数的名称，例如 summary 提供了有意义的名称。 如果不存在，则参数可命名为 `param0`，`param1`等。

"""
单变量局部线性趋势模型
"""


class LocalLinearTrend(sm.tsa.statespace.MLEModel):
    def __init__(self, endog):
        # Model order
        k_states = k_posdef = 2

        # 初始化状态空间
        super(LocalLinearTrend, self).__init__(
            endog,
            k_states=k_states,
            k_posdef=k_posdef,
            initialization='approximate_diffuse',
            loglikelihood_burn=k_states)

        # 初始化矩阵
        self.ssm['design'] = np.array([1, 0])
        self.ssm['transition'] = np.array([[1, 1], [0, 1]])
        self.ssm['selection'] = np.eye(k_states)

        # 缓存索引
        self._state_cov_idx = ('state_cov', ) + np.diag_indices(k_posdef)

    @property
    def param_names(self):
        return ['sigma2.measurement', 'sigma2.level', 'sigma2.trend']

    @property
    def start_params(self):
        return [np.std(self.endog)] * 3

    def transform_params(self, unconstrained):
        return unconstrained**2

    def untransform_params(self, constrained):
        return constrained**0.5

    def update(self, params, *args, **kwargs):
        params = super(LocalLinearTrend, self).update(params, *args, **kwargs)

        # 观测协方差
        self.ssm['obs_cov', 0, 0] = params[0]

        # 状态协方差
        self.ssm[self._state_cov_idx] = params[1:]


# 使用这个简单的模型，我们可以从局部线性趋势模型中估计参数。 下面的示例是来自 Commandeur 和 Koopman（2007）第3.4节，
# 对芬兰的机动车死亡人数进行了建模。


import requests
from io import BytesIO
from zipfile import ZipFile

# 加载数据集
ck = requests.get(
    'http://staff.feweb.vu.nl/koopman/projects/ckbook/OxCodeAll.zip').content
zipped = ZipFile(BytesIO(ck))
df = pd.read_table(
    BytesIO(
        zipped.read('OxCodeIntroStateSpaceBook/Chapter_2/NorwayFinland.txt')),
    skiprows=1,
    header=None,
    sep='\s+',
    engine='python',
    names=['date', 'nf', 'ff'])

# 由于我们定义局部线性趋势模型是从 `MLEModel` 扩展而来，因此 `fit()` 方法可直接使用，就像在 statsmodels 中的其他极大似然类中一样。 
# 同样，返回的结果类支持许多相同的 post-estimation（后估计）结果，例如 `summary` 方法。
#

# 加载数据集
df.index = pd.date_range(
    start='%d-01-01' % df.date[0], end='%d-01-01' % df.iloc[-1, 0], freq='AS')

# 对数转换
df['lff'] = np.log(df['ff'])

# 设置模型
mod = LocalLinearTrend(df['lff'])

# 使用 MLE 拟合（记得我们拟合了三个方差参数）
res = mod.fit(disp=False)
print(res.summary())

# 最后，我们可以做 post-estimation（后估计）预测和预测。注意，可以将结束时间指定为日期。

# 执行预测和预测
predict = res.get_prediction()
forecast = res.get_forecast('2014')

fig, ax = plt.subplots(figsize=(10, 4))

# 绘制结果
df['lff'].plot(ax=ax, style='k.', label='Observations')
predict.predicted_mean.plot(ax=ax, label='One-step-ahead Prediction')
predict_ci = predict.conf_int(alpha=0.05)
predict_index = np.arange(len(predict_ci))
ax.fill_between(
    predict_index[2:],
    predict_ci.iloc[2:, 0],
    predict_ci.iloc[2:, 1],
    alpha=0.1)

forecast.predicted_mean.plot(ax=ax, style='r', label='Forecast')
forecast_ci = forecast.conf_int()
forecast_index = np.arange(len(predict_ci), len(predict_ci) + len(forecast_ci))
ax.fill_between(
    forecast_index, forecast_ci.iloc[:, 0], forecast_ci.iloc[:, 1], alpha=0.1)

# 简化图像
ax.set_ylim((4, 8))
legend = ax.legend(loc='lower left')

# ### 参考文献
#
#     Commandeur, Jacques J. F., and Siem Jan Koopman. 2007.
#     状态空间时间序列分析简介.
#     Oxford ; New York: Oxford University Press.
#
#     Durbin, James, and Siem Jan Koopman. 2012.
#     通过状态空间方法进行时间序列分析: Second Edition.
#     Oxford University Press.
