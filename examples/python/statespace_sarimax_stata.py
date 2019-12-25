# coding: utf-8

# DO NOT EDIT
# Autogenerated from the notebook statespace_sarimax_stata.ipynb.
# Edit the notebook and then sync the output with this file.
#
# flake8: noqa
# DO NOT EDIT

# # SARIMAX：简介

# 这个笔记复制了 Stata 的 ARIMA 时间序列估计和后估计文档中的示例。
#
# 首先，我们复制四个估计示例 http://www.stata.com/manuals13/tsarima.pdf:
#
# 1.美国批发价格指数（WPI）数据集上的 ARIMA(1,1,1) 模型。
# 2.示例1的变体，在 ARIMA(1,1,1)）规范中添加了 MA(4)项，以实现附加季节性影响。
# 3.每月航空公司数据的 ARIMA(2,1,0) x (1,1,0,12) 模型。 这个例子允许一个乘法季节性影响。
# 4.具有外生回归变量的 ARMA(1,1) 模型； 将消费描述为自回归过程，在此过程中，货币供应量是被假定为一个解释变量。
# 
#
# 其次，我们从 http://www.stata.com/manuals13/tsarimapostestimation.pdf 复制来演示后估计性能。 以示例 4 中的模型作为演示：
#
# 1.提前 one-step 样本内预测
# 2.提前 n-step 样本外预测
# 3.提前 n-step 样本内动态预测

import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
import matplotlib.pyplot as plt
from datetime import datetime
import requests
from io import BytesIO

# ### ARIMA 示例 1: Arima
#
# 
# 从示例 2 的图表中可以看出，批发价格指数 (WPI) 随时间增长（即不平稳）。 因此，ARMA 模型不是一个很好的规范。 
# 在第一个示例中，我们认为一个模型，其中，在该模型中原始时间序列被假定为阶次积分
#
# 1 因此假设差异是固定的，并拟合具有一个自回归滞后和一个移动平均滞后并有一个截距项的模型。
#
# 然后假定的数据处理:
#
# $$
# \Delta y_t = c + \phi_1 \Delta y_{t-1} + \theta_1 \epsilon_{t-1} +
# \epsilon_{t}
# $$
#
# 其中 $c$ 是 ARMA 模型的截距，$\Delta$ 是一阶差分运算符，我们假定 $\epsilon_{t} \sim N(0, \sigma^2)$。
# 可以将其重写为强调滞后多项式（在下面的示例2中将很有用）
#
# $$
# (1 - \phi_1 L ) \Delta y_t = c + (1 + \theta_1 L) \epsilon_{t}
# $$
#
# 其中 $L$ 是滞后运算符。
#
# 请注意，存在一个差异 —— Stata 输出的模型与下方输出的 Stata估计模型：
#
# $$
# (\Delta y_t - \beta_0) = \phi_1 ( \Delta y_{t-1} - \beta_0) + \theta_1
# \epsilon_{t-1} + \epsilon_{t}
# $$
#
# 其中 $\beta_0$ 是程序 $y_t$ 的平均值。该模型等效于 statsmodels SARIMAX 类中估计的模型，但是解释不同。
# 要查看等效项，请注意：
#
# $$
# (\Delta y_t - \beta_0) = \phi_1 ( \Delta y_{t-1} - \beta_0) + \theta_1
# \epsilon_{t-1} + \epsilon_{t} \\
# \Delta y_t = (1 - \phi_1) \beta_0 + \phi_1 \Delta y_{t-1} + \theta_1
# \epsilon_{t-1} + \epsilon_{t}
# $$
#
# 因此 $c = (1 - \phi_1) \beta_0$.

# 数据集
wpi1 = requests.get('https://www.stata-press.com/data/r12/wpi1.dta').content
data = pd.read_stata(BytesIO(wpi1))
data.index = data.t

# 拟合模型
mod = sm.tsa.statespace.SARIMAX(data['wpi'], trend='c', order=(1, 1, 1))
res = mod.fit(disp=False)
print(res.summary())

# 因此，对于上述过程极大似然估计意味着，我们有:
#
# $$
# \Delta y_t = 0.1050 + 0.8740 \Delta y_{t-1} - 0.4206 \epsilon_{t-1} +
# \epsilon_{t}
# $$
#
# 其中 $\epsilon_{t} \sim N(0, 0.5226)$. Finally, 最后，回想一下 $c = (1 - \phi_1) \beta_0$, 
# 在这里 $c = 0.1050$ 且 $\phi_1 = 0.8740$ 。 为了与 Stata 的输出进行比较，我们可以计算出平均值：
#
# $$\beta_0 = \frac{c}{1 - \phi_1} = \frac{0.1050}{1 - 0.8740} = 0.83$$
#
# **注意**：这些值与 Stata 文档中的值略有不同，因为 statsmodels 的优化器在此处慧生成一个更高似然的参数。尽管如此，它们非常接近。



# ### ARIMA 示例 2: 附加季节性影响的 ARIMA 模型 
#
# $$
# \Delta y_t = c + \phi_1 \Delta y_{t-1} + \theta_1 \epsilon_{t-1} +
# \theta_4 \epsilon_{t-4} + \epsilon_{t}
# $$
#
# 该模型的新部分是允许有年度季节性影响（即使周期性为4，因为数据集是季度性的，所以它也是年度的）。 第二个区别是该模型使用数据日志而不是水平。
# 
#
# 在估计数据集之前，图形显示：
#
# 1.时间序列（以日志为单位）
# 2.时间序列的第一个差异（以日志为单位）
# 3.自相关函数
# 4.偏自相关函数
#
# 从前两个图表中，我们注意到原始时间序列似乎不是平稳的，而一阶差异却是平稳的。要么根据数据的一阶差异估计一个 ARMA 模型，
# 要么估计一个带有一阶积分的 ARIMA 模型（回想一下，我们采用的是后一种方法）。最后两个图支持使用 ARMA(1,1,1) 模型。


# 数据集
data = pd.read_stata(BytesIO(wpi1))
data.index = data.t
data['ln_wpi'] = np.log(data['wpi'])
data['D.ln_wpi'] = data['ln_wpi'].diff()

# 图形数据
fig, axes = plt.subplots(1, 2, figsize=(15, 4))

# 水平
axes[0].plot(data.index._mpl_repr(), data['wpi'], '-')
axes[0].set(title='US Wholesale Price Index')

# 日志差异
axes[1].plot(data.index._mpl_repr(), data['D.ln_wpi'], '-')
axes[1].hlines(0, data.index[0], data.index[-1], 'r')
axes[1].set(title='US Wholesale Price Index - difference of logs')

# 图形数据
fig, axes = plt.subplots(1, 2, figsize=(15, 4))

fig = sm.graphics.tsa.plot_acf(data.iloc[1:]['D.ln_wpi'], lags=40, ax=axes[0])
fig = sm.graphics.tsa.plot_pacf(data.iloc[1:]['D.ln_wpi'], lags=40, ax=axes[1])

# 为了了解如何在 statsmodels 中指定此模型，首先回想示例 1，我们使用以下代码来指定 ARIMA(1,1,1) 模型：
#
# ```python
# mod = sm.tsa.statespace.SARIMAX(data['wpi'], trend='c', order=(1,1,1))
# ```
#
# “ order”参数是元组的形式“（AR 规范，整合阶，MA 规范）”。 整合阶必须是整数（例如，在这里我们假设一阶整合，
# 因此将其指定为1。在基础数据已经固定的纯ARMA模型中，它将为0）。
#
#
# 对于 AR 规范和 MA 规范组件，有两种可能性。首先是指定相应滞后多项式的 **maximum degree** ，在这种情况下，该组件是整数。
# 例如，如果我们想指定一个 ARIMA(1,1,4) ，我们将使用：
#
# ```python
# mod = sm.tsa.statespace.SARIMAX(data['wpi'], trend='c', order=(1,1,4))
# ```
#
# 相应的数据处理将是:
#
# $$
# y_t = c + \phi_1 y_{t-1} + \theta_1 \epsilon_{t-1} + \theta_2
# \epsilon_{t-2} + \theta_3 \epsilon_{t-3} + \theta_4 \epsilon_{t-4} +
# \epsilon_{t}
# $$
#
# 或者
#
# $$
# (1 - \phi_1 L)\Delta y_t = c + (1 + \theta_1 L + \theta_2 L^2 + \theta_3
# L^3 + \theta_4 L^4) \epsilon_{t}
# $$
#
# 当指定参数作为滞后多项式的最高阶次给出时，则意味着提高到所有多项式包含阶次。 请注意，这不是我们要使用的模型，
# 因为它包含 $\epsilon_{t-2}$ 和 $\epsilon_{t-3}$ 项，在这里我们不希望使用。
#
# 我们想要的是一个多项式，带有第 1 和第 4 阶次项，而没有第2 和第 3 阶次项。为此，我们需要为规范参数提供一个元组，
# 其中元组描述 **the lag polynomial itself**。 特别是，在这里我们要使用：
# 
#
# ```python
# ar = 1          # this is the maximum degree specification
# ma = (1,0,0,1)  # this is the lag polynomial specification
# mod = sm.tsa.statespace.SARIMAX(data['wpi'], trend='c',
# order=(ar,1,ma)))
# ```
#
# 这给出以下程式来做数据处理:
#
# $$
# \Delta y_t = c + \phi_1 \Delta y_{t-1} + \theta_1 \epsilon_{t-1} +
# \theta_4 \epsilon_{t-4} + \epsilon_{t} \\
# (1 - \phi_1 L)\Delta y_t = c + (1 + \theta_1 L + \theta_4 L^4)
# \epsilon_{t}
# $$
#
# 这是我们想要的.

# 拟合模型
mod = sm.tsa.statespace.SARIMAX(data['ln_wpi'], trend='c', order=(1, 1, 1))
res = mod.fit(disp=False)
print(res.summary())

# ### ARIMA 示例 3: Airline Model
#
# 在前面的示例中，我们以“加法”方式包括了季节性影响，这意味着我们添加一项允许进程依赖第 4 MA 滞后。
# 取而代之的是，我们希望以“乘法”方式对季节效应进行建模。我们通常将模型写成 ARIMA $(p,d,q)\times (P,D,Q)_s$，
# 其中小写字母表示非季节性成分的规范，大写字母表示季节性成分的规范； $s$ 是季节的周期性（例如，季度数据通常为4，月度数据通常为12）。
# 数据处理可以一般写为
#
# $$
# \phi_p (L) \tilde \phi_P (L^s) \Delta^d \Delta_s^D y_t = A(t) + \theta_q
# (L) \tilde \theta_Q (L^s) \epsilon_t
# $$
#
# 其中:
#
# - $\phi_p (L)$ 是非季节性自回归滞后多项式
# - $\tilde \phi_P (L^s)$ 是季节性自回归滞后多项式
# - $\Delta^d \Delta_s^D y_t$ 是时间序列, 相差 $d$ 次,而季节性相差 $D$ 次.
# - $A(t)$ 是趋势性多项式 (包含截距)
# - $\theta_q (L)$ 是非季节性移动平均滞后多项式
# - $\tilde \theta_Q (L^s)$ 是季节性移动平均滞后多项式
#
# 有时我们可以改写为:
#
# $$
# \phi_p (L) \tilde \phi_P (L^s) y_t^* = A(t) + \theta_q (L) \tilde
# \theta_Q (L^s) \epsilon_t
# $$
#
# 其中 $y_t^* = \Delta^d \Delta_s^D y_t$. 这强调了在简单的情况下，我们采用差异（这里是非季节性和季节性）来使数据稳定之后，
# 所得到的模型是一个 ARMA 模型。
#
# 例如，考虑带有截距的航空公司模型 ARIMA $(2,1,0) \times(1,1,0)_{12}$。数据处理可以按上面的程式写成：
#
# $$
# (1 - \phi_1 L - \phi_2 L^2) (1 - \tilde \phi_1 L^{12}) \Delta
# \Delta_{12} y_t = c + \epsilon_t
# $$
#
# 在这里有:
#
# - $\phi_p (L) = (1 - \phi_1 L - \phi_2 L^2)$
# - $\tilde \phi_P (L^s) = (1 - \phi_1 L^12)$
# - $d = 1, D = 1, s=12$ 表示 $y_t^*$ 是从第 1 阶差异到第 12 阶差异派生的
# - $A(t) = c$ 是 *恒定* 趋势性多项式（即一个截距）
# - $\theta_q (L) = \tilde \theta_Q (L^s) = 1$ (即没有移动平均效应）
#
# 在时间序列变量的前面看到两个滞后多项式可能仍然令人困惑，但是请注意，我们可以将滞后多项式相乘以得到以下模型：
#
# $$
# (1 - \phi_1 L - \phi_2 L^2 - \tilde \phi_1 L^{12} + \phi_1 \tilde \phi_1
# L^{13} + \phi_2 \tilde \phi_1 L^{14} ) y_t^* = c + \epsilon_t
# $$
#
# 可以重写为:
#
# $$
# y_t^* = c + \phi_1 y_{t-1}^* + \phi_2 y_{t-2}^* + \tilde \phi_1
# y_{t-12}^* - \phi_1 \tilde \phi_1 y_{t-13}^* - \phi_2 \tilde \phi_1
# y_{t-14}^* + \epsilon_t
# $$
#
# 这类似于示例 2 中的附加季节性的模型，但是在自回归滞后项前面的系数实际上是基于季节性和非季节性参数的组合
#
# 
# 在 statsmodels 中指定模型只需添加 `seasonal_order` 参数即可，该参数可使用元祖 '（季节性 AR 规范，季节性整合阶，季节性 MA，季节周期性）'。 
# 如前所述，季节性 AR 和 MA 规范可以表示为最大多项式或滞后多项式。 季节周期性是整数。
#
# 对于带有截距的航空公司模型 ARIMA $(2,1,0) \times (1,1,0)_{12}$ 的代码是:
#
# ```python
# mod = sm.tsa.statespace.SARIMAX(data['lnair'], order=(2,1,0),
# seasonal_order=(1,1,0,12))
# ```

# 数据集
air2 = requests.get('https://www.stata-press.com/data/r12/air2.dta').content
data = pd.read_stata(BytesIO(air2))
data.index = pd.date_range(
    start=datetime(data.time[0], 1, 1), periods=len(data), freq='MS')
data['lnair'] = np.log(data['air'])

# 拟合模型
mod = sm.tsa.statespace.SARIMAX(
    data['lnair'],
    order=(2, 1, 0),
    seasonal_order=(1, 1, 0, 12),
    simple_differencing=True)
res = mod.fit(disp=False)
print(res.summary())

# 注意，在这里我们使用另外一个参数 `simple_differencing = True`。 这个参数控制在ARIMA 模型中整合阶是如何处理的。 
# 如果 `simple_differencing = True`，那么以 `endog` 提供的时间序列在字面上会有所不同，并且拟合 ARMA 模型将生成新的时间序列。 
# 这意味着差分程序会损失许多开始的时期，然而仍需要将结果与其他软件包进行比较（例如，Stata 的`arima`，通常使用简单的差分），
# 或者季节周期性较大。
# 
#
# 参数默认值为 `simple_differencing=False`，在这种情况下，集成组件将以状态空间公式的一部分来实现，并且所有原始数据都可以用于估计。


# ### ARIMA 示例 4: ARMAX (Friedman)
#
# 该模型演示了解释变量的使用（ARMAX 的 X 部分）。 当包含外生回归变量时，SARIMAX 模块使用“带有 SARIMA 误差的回归”的概念
# （有关带有 ARIMA 误差的回归与另类规范的详细信息，请参见http://robjhyndman.com/hyndsight/arimax/），因此该模型可指定为：
# 
#
# $$
# y_t = \beta_t x_t + u_t \\
#         \phi_p (L) \tilde \phi_P (L^s) \Delta^d \Delta_s^D u_t = A(t) +
#             \theta_q (L) \tilde \theta_Q (L^s) \epsilon_t
# $$
#
# 注意，第一个方程只是线性回归，第二个方程将进程描述为 SARIMA 的误差成分（如示例 3 中所述）。规范的原因之一是估计的参数具有其固有的解释。
#
# 这个规范嵌套了许多更简单的规范。 例如，带有 AR(2) 的回归是:
#
# $$
# y_t = \beta_t x_t + u_t \\
# (1 - \phi_1 L - \phi_2 L^2) u_t = A(t) + \epsilon_t
# $$
#
# 在这个实例中，可以把模型看成为带有 ARMA(1,1) 误差的回归，程序可以写成
#
# $$
# \text{consump}_t = \beta_0 + \beta_1 \text{m2}_t + u_t \\
# (1 - \phi_1 L) u_t = (1 - \theta_1 L) \epsilon_t
# $$
#
# 请注意，如上面的示例 1 中所述，$\beta_0$  与 `trend='c'' 指定的截距不是同一件事。 尽管在上面的示例中，我们通过趋势性多项式估计模型的截距，
# 但在这里，我们演示了如何通过给外生数据集增加一个常量来估计 $beta_0$ 本身。 输出的结果，其中 $beta_0$ 可看成是 `const`，而上面的截距 $c$ 
# 可看成是 `intercept`。

# 数据集
friedman2 = requests.get(
    'https://www.stata-press.com/data/r12/friedman2.dta').content
data = pd.read_stata(BytesIO(friedman2))
data.index = data.time

# 内生、外生变量
endog = data.loc['1959':'1981', 'consump']
exog = sm.add_constant(data.loc['1959':'1981', 'm2'])

# 拟合模型
mod = sm.tsa.statespace.SARIMAX(endog, exog, order=(1, 0, 1))
res = mod.fit(disp=False)
print(res.summary())

# ### ARIMA 后估计: 示例 1 - 动态预测
#
# 下面描述了 statsmodels 的 SARIMAX 模型的一些后估计功能。
#
# 首先，使用示例中的模型，我们使用*不包括最后几个观察值*的数据来估计参数（这是一个人工的示例，但可以研究样本外预测的性能，
# 并有助于与 Stata 文档进行比较 ）。

# 数据集
raw = pd.read_stata(BytesIO(friedman2))
raw.index = raw.time
data = raw.loc[:'1981']

# 内生、外生变量
endog = data.loc['1959':, 'consump']
exog = sm.add_constant(data.loc['1959':, 'm2'])
nobs = endog.shape[0]

# 拟合模型
mod = sm.tsa.statespace.SARIMAX(
    endog.loc[:'1978-01-01'], exog=exog.loc[:'1978-01-01'], order=(1, 0, 1))
fit_res = mod.fit(disp=False)
print(fit_res.summary())

# 接下来，我们要获取整个数据集的结果，但要使用估计的参数（在数据的子集上）。

mod = sm.tsa.statespace.SARIMAX(endog, exog=exog, order=(1, 0, 1))
res = mod.filter(fit_res.params)

# 首先，在此处运用 `predict` 命令以获取样本内预测。使用 `full_results = True` 参数来计算置信区间（`predict` 的默认输出只是预测值）。
#
# 没有其他参数，`predict` 将返回整个样本的提前 one-step 样本内预测值。

# 提前 one-step 样本内预测
predict = res.get_prediction()
predict_ci = predict.conf_int()

# 我们还可以获得 *动态预测*。 提前 one-step 预测使用每个步骤中的内生变量真实值来预测下一个样本内值。动态预测使用一步到位预测直到数据集中的某个点
# （由 `dynamic` 参数来指定）；之后，将使用先前的 *predicted* 内生变量值代替每个新预测部分的真实内生变量值。
# 
#
# `dynamic` 参数用于指定 `start` 参数的相对偏移。 如果 `start` 参数未指定，则假定为 `0`。
#
# 在这里，我们从1978年第一季度开始进行动态预测.

# 动态预测
predict_dy = res.get_prediction(dynamic='1978-01-01')
predict_dy_ci = predict_dy.conf_int()

# 我们可以绘制提前 one-step 预测和动态预测（以及相应的置信区间），来查看他们的相关性。 请注意，直到开始进行动态预测（1978：Q1）为止，两者都是相同的。


# 绘图
fig, ax = plt.subplots(figsize=(9, 4))
npre = 4
ax.set(
    title='Personal consumption', xlabel='Date', ylabel='Billions of dollars')

# 绘制数据点
data.loc['1977-07-01':, 'consump'].plot(ax=ax, style='o', label='Observed')

# 绘制预测结果
predict.predicted_mean.loc['1977-07-01':].plot(
    ax=ax, style='r--', label='One-step-ahead forecast')
ci = predict_ci.loc['1977-07-01':]
ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], color='r', alpha=0.1)
predict_dy.predicted_mean.loc['1977-07-01':].plot(
    ax=ax, style='g', label='Dynamic forecast (1978)')
ci = predict_dy_ci.loc['1977-07-01':]
ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], color='g', alpha=0.1)

legend = ax.legend(loc='lower right')

# 最后绘制预测 *误差* ，显然，正如我们怀疑的那样，提前 one-step 预测相对更好

# 预测误差

# 绘图
fig, ax = plt.subplots(figsize=(9, 4))
npre = 4
ax.set(title='Forecast error', xlabel='Date', ylabel='Forecast - Actual')

# 提前 one-step 样本内预测和 95% 置信区间
predict_error = predict.predicted_mean - endog
predict_error.loc['1977-10-01':].plot(ax=ax, label='One-step-ahead forecast')
ci = predict_ci.loc['1977-10-01':].copy()
ci.iloc[:, 0] -= endog.loc['1977-10-01':]
ci.iloc[:, 1] -= endog.loc['1977-10-01':]
ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], alpha=0.1)

# 动态预测和 95% 置信区间
predict_dy_error = predict_dy.predicted_mean - endog
predict_dy_error.loc['1977-10-01':].plot(
    ax=ax, style='r', label='Dynamic forecast (1978)')
ci = predict_dy_ci.loc['1977-10-01':].copy()
ci.iloc[:, 0] -= endog.loc['1977-10-01':]
ci.iloc[:, 1] -= endog.loc['1977-10-01':]
ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], color='r', alpha=0.1)

legend = ax.legend(loc='lower left')
legend.get_frame().set_facecolor('w')
