# coding: utf-8

# DO NOT EDIT
# Autogenerated from the notebook discrete_choice_overview.ipynb.
# Edit the notebook and then sync the output with this file.
#
# flake8: noqa
# DO NOT EDIT

# # 离散选择模型概述

import numpy as np
import statsmodels.api as sm

# ## 数据
#
# 从Spector 和 Mazzeo（1980）加载数据。 示例来自格林的《计量经济学分析》。 21（第5版）。


spector_data = sm.datasets.spector.load()
spector_data.exog = sm.add_constant(spector_data.exog, prepend=False)

# 检查数据:

print(spector_data.exog[:5, :])
print(spector_data.endog[:5])

# ## 线性概率模型 (OLS)

lpm_mod = sm.OLS(spector_data.endog, spector_data.exog)
lpm_res = lpm_mod.fit()
print('Parameters: ', lpm_res.params[:-1])

# ## Logit 模型

logit_mod = sm.Logit(spector_data.endog, spector_data.exog)
logit_res = logit_mod.fit(disp=0)
print('Parameters: ', logit_res.params)

# 边际效应

margeff = logit_res.get_margeff()
print(margeff.summary())

# 与下面介绍的所有离散数据模型一样，我们可以打印出一个不错的 summary 结果：

print(logit_res.summary())

# ## Probit 模型

probit_mod = sm.Probit(spector_data.endog, spector_data.exog)
probit_res = probit_mod.fit()
probit_margeff = probit_res.get_margeff()
print('Parameters: ', probit_res.params)
print('Marginal effects: ')
print(probit_margeff.summary())

# ## 多项式 Logit

# 加载的数据来自美国国家选举研究:

anes_data = sm.datasets.anes96.load()
anes_exog = anes_data.exog
anes_exog = sm.add_constant(anes_exog, prepend=False)

# 检查数据:

print(anes_data.exog[:5, :])
print(anes_data.endog[:5])

# 拟合 MNL 模型:

mlogit_mod = sm.MNLogit(anes_data.endog, anes_exog)
mlogit_res = mlogit_mod.fit()
print(mlogit_res.params)

# ## Poisson
#
# 加载 Rand 数据。 请注意，此示例与 Cameron 和 Trivedi 所著的 “微观计量经济学”树种的表 20.5 相似，但是由于数据的微小变化而略有不同

rand_data = sm.datasets.randhie.load()
rand_exog = rand_data.exog.view(float).reshape(len(rand_data.exog), -1)
rand_exog = sm.add_constant(rand_exog, prepend=False)

# 拟合 Poisson 模型:

poisson_mod = sm.Poisson(rand_data.endog, rand_exog)
poisson_res = poisson_mod.fit(method="newton")
print(poisson_res.summary())

# ## 负二项式
#
# 负二项式模型给出的结果略有不同。

mod_nbin = sm.NegativeBinomial(rand_data.endog, rand_exog)
res_nbin = mod_nbin.fit(disp=False)
print(res_nbin.summary())

# ## 替代求解器
#
# 拟合离散数据 MLE 模型的默认方法是 Newton-Raphson。 您可以使用 “method” 参数来使用其他求解器：

mlogit_res = mlogit_mod.fit(method='bfgs', maxiter=100)
print(mlogit_res.summary())
