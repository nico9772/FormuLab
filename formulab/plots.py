import matplotlib.pyplot as plt

from formulab import config as cfg

def common(fig, textsize=cfg.textsize, xlabel='', ylabel='', title=''):
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(prop={'size': textsize})
    
    plt.grid()
    
    fig.canvas.toolbar_position=cfg.toolbar_position
    fig.canvas.header_visible=cfg.header_visible
    return fig

def plot(x, y, ref=0, zorder=0, color=cfg.plotcolor, linewidth=cfg.linewidth, textsize=cfg.textsize, label='', xlabel='', ylabel='', title=''):
    fig=plt.figure(ref)
    plt.plot(x, y, zorder=zorder, label=label, color=color, linewidth=linewidth)
    return common(fig, textsize=textsize, xlabel=xlabel, ylabel=ylabel, title=title)

def err_scatter(x, y, xerr, yerr, ref=0, zorder=0, dotsize=cfg.dotsize, color=cfg.scattercolor, ecolor=cfg.ecolor, elinewidth=cfg.elinewidth, capsize=cfg.capsize, textsize=cfg.textsize, label='', xlabel='', ylabel='', title=''):
    fig=plt.figure(ref)
    
    plt.errorbar(x,y, xerr=xerr, yerr=yerr, zorder=zorder, label=label, fmt='.', markersize=dotsize, color=color, ecolor=ecolor, elinewidth=elinewidth, capsize=capsize)
    return common(fig, textsize=textsize, xlabel=xlabel, ylabel=ylabel, title=title)

def scatter(x, y, ref=0, zorder=0, dotsize=cfg.dotsize, color=cfg.scattercolor, textsize=cfg.textsize, label='', xlabel='', ylabel='', title=''):
    fig=plt.figure(ref)
    
    plt.scatter(x, y, zorder=zorder, label=label, marker='o', s=dotsize, color=color)
    return common(fig, textsize=textsize, xlabel=xlabel, ylabel=ylabel, title=title)