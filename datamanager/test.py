import ast
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np


path = "/Users/danielperry/Documents/EngSci/Year4Summer/Arts et Metier/PIMM development/PIMM-LDV-Scanner/sample_data/experiments/trial7.txt"
print("Reading data from: " + path)
with open(path) as f:
    data = ast.literal_eval(f.read())
    f.close()

print("Processing data...")
## Extract data from dictionary
scan_path = data['scan_path']
response_data = data['response_data']
reference = data['reference']

x_values = list(set([x[0] for x in scan_path]))
y_values = list(set([x[1] for x in scan_path]))
x_values.sort()
y_values.sort()

def get_response_at_time(t):
    data_array = np.zeros((len(x_values), len(y_values)))
    for i, coordinate in enumerate(scan_path):
        # print(i)
        # print(coordinate)
        grid_index = (x_values.index(coordinate[0]), y_values.index(coordinate[1]))
        # print(grid_index)
        x, y = grid_index
        # print(x, y)
        data_array[x, y] = response_data[i][t]
    return data_array

print("Plotting data...")
# for time in range(0, len(response_data[0])):
# for time in range(0, 500):
#     fig, ax = plt.subplots()
#     im = ax.imshow(get_response_at_time(time), cmap='hot', interpolation='nearest')
#     plt.show(block = False)
#     plt.pause(0.05)
#     plt.close('all')


### animation
print("Animating data...")
num_frames = min([len(x) for x in self.data_manager.response_data])
fps = 500
length = num_frames/fps

fig = plt.figure()
time = 0
response = get_response_at_time(time)
im = plt.imshow(response, cmap='hot', interpolation='nearest', vmin=-1, vmax=1)
title = plt.title(f"Index: {time} of {num_frames}")
plt.colorbar()

def animate(time):
    time += 1
    response = get_response_at_time(time)
    im.set_array(response)
    title = plt.title(f"Index: {time} of {num_frames}")
    return [im, title]

plt.close('all')

# anim = animation.FuncAnimation(fig, animate, frames=range(0, len(response_data[0])), interval=50, blit=True)
anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1000/fps, blit=False, repeat=False)

## Save animation
print("Saving animation...")
anim.save('test_anim.mp4', fps=fps, extra_args=['-vcodec', 'libx264'])
print("Animation saved to: test_anim.mp4")

# plt.show(block = False)
# plt.close('all')
    