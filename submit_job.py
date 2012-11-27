#!/usr/bin/env python

import os
import sys
import argparse
import datetime

# The project path is always the directory of the script
PROJECT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))

matlabCommand = """
matlab -nodisplay -nodesktop <<EOD
cd {projectPath:s};
trainParams.wordDataset     = {wordDataset!r};
trainParams.batchFilePrefix = {batchFilePrefix!r};
trainParams.maxPass         = {maxPass:d};
trainParams.maxIter         = {maxIter:d};
trainParams.wReg            = {wReg:.3E};
trainParams.iReg            = {iReg:.3E};
trainParams.outputPath      = {outputPath!r};
train;
EOD
"""

qsubCommand = 'cat <<EOF | nlpsub --mail=bea --name={name!r} --log-dir={outputPath!r} --clobber --priority=high {optionalArgs} {command}EOF'

parser = argparse.ArgumentParser(description="Submit training job to NLP cluster")
parser.add_argument('--wordset', help='the word vector dataset to use')
parser.add_argument('--trainset', help='the prefix of the image batches to use')
parser.add_argument('--maxPass', help='the number of passes through the training data', type=int)
parser.add_argument('--maxIter', help='the number of iterations over a training batch', type=int)
parser.add_argument('--wordReg', help='the regularization param for words', type=float)
parser.add_argument('--imageReg', help='the regularization param for images', type=float)
parser.add_argument('-m', '--machine', nargs='*', help='machines to use')
parser.add_argument('--mem', help='memory to allocate')
parser.add_argument('-i', '--jobId', help='the name of the job, also used as output folder')
parser.add_argument('--dry-run', help='do a dry run (do not actually submit the job)', action="store_true")
parser.add_argument('-v', '--verbose', help='show command that will be executed', action="store_true")
args = parser.parse_args()

jobId = args.jobId or ('zsl-' + datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S_%f"))
outputPath = os.path.join(PROJECT_PATH, jobId)

arguments = {
    'wordDataset':     args.wordset or 'icml',
    'batchFilePrefix': args.trainset or 'mini_batch',
    'maxPass':         args.maxPass or 3,
    'maxIter':         args.maxIter or 2,
    'wReg':            args.wordReg or 1E-3,
    'iReg':            args.imageReg or 1E-6,
    'projectPath':     PROJECT_PATH,
    'outputPath':      outputPath,
}

optionalArgs = ''
if args.machine:
    optionalArgs += ' --hosts={0!r} '.format(','.join(args.machine))
if args.mem:
    optionalArgs += ' --mem={0} '.format(args.mem)
if args.verbose:
    optionalArgs += ' --verbose '
if args.dry_run:
    optionalArgs += ' --dry-run '

qsubArguments = {
    'name':         jobId,
    'outputPath':   outputPath,
    'optionalArgs': optionalArgs.strip(),
    'command':      matlabCommand.format(**arguments),
}

finalCommand = qsubCommand.format(**qsubArguments)
if args.verbose:
    print '$ ' + finalCommand

# if none of the arguments exist, don't submit job
atLeastOne = False
argDict = vars(args)
for argKey in argDict:
    if argDict[argKey] and argKey != 'verbose':
        atLeastOne = True
        break

if atLeastOne:
    #if not os.path.exists(outputPath):
    #    os.makedirs(outputPath)
    os.system(finalCommand)
else:
    print '>>>> No argument was given. Not submitting job. You can see the way the argument would be constructed.'
