import os
import math
import torch
import pickle
import argparse
import torchvision.utils as vutils
from denseflow.utils import dataset_save_latent

# Data
from data.data import get_data, get_data_id, add_data_args

# Model
from model.model_flow import get_model, get_model_id, add_model_args
from denseflow.distributions import DataParallelDistribution

###########
## Setup ##
###########

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default=None)
parser.add_argument('--k', type=int, default=None)
parser.add_argument('--kbs', type=int, default=None)
parser.add_argument('--batch_size', type=int, default=64)
parser.add_argument('--double', type=eval, default=False)
parser.add_argument('--seed', type=int, default=0)
eval_args = parser.parse_args()

path_args = '{}/args.pickle'.format(eval_args.model)
path_check = '{}/check/checkpoint.pt'.format(eval_args.model)

torch.manual_seed(eval_args.seed)

###############
## Load args ##
###############

with open(path_args, 'rb') as f:
    args = pickle.load(f)

##################
## Specify data ##
##################

train_loader, eval_loader, data_shape = get_data(args)

# Adjust args
args.batch_size = eval_args.batch_size

###################
## Specify model ##
###################

model = get_model(args, data_shape=data_shape)
if args.parallel == 'dp':
    model = DataParallelDistribution(model)
checkpoint = torch.load(path_check)
model.load_state_dict(checkpoint['model'])
print('Loaded weights for model at {}/{} epochs'.format(checkpoint['current_epoch'], args.epochs))

path_new_dataset = '../../data/{}_new/'.format(args.dataset)
if not os.path.exists(os.path.dirname(path_new_dataset)):
    os.mkdir(os.path.dirname(path_new_dataset))
    os.mkdir(os.path.dirname(path_new_dataset+'train/'))
    os.mkdir(os.path.dirname(path_new_dataset+'eval/'))
else: 
    raise NameError('Dataset already commputed')
############
## Loglik ##
############

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = model.to(device)
model = model.eval()
if eval_args.double: model = model.double()

eval_str = 'Saving latent'
print('Starting Saving Latent')
dataset_save_latent(model, train_loader, device, path_new_dataset, train=True,  double=False, verbose=True)
dataset_save_latent(model, eval_loader, device, path_new_dataset, train=False, double=False, verbose=True)
print('Done')


path_loglik = '{}/loglik/{}_ep{}.txt'.format(eval_args.model, eval_str, checkpoint['current_epoch'])
if not os.path.exists(os.path.dirname(path_loglik)):
    os.mkdir(os.path.dirname(path_loglik))

with open(path_loglik, 'w') as f:
    f.write(str(bpd))
