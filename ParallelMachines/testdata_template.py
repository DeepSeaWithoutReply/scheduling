import pandas as pd
import yaml
import random

file = open(r'config.yaml','r',encoding='utf-8')
file_data = file.read()
file.close()
config = yaml.load(file_data,Loader=yaml.FullLoader)

job_id = [ i for i in range(config["jobs"])]
machine_id = [i for i in range(config["machines"])]

# 工作的相关属性
release_time = []
due_time = []
if config["has_release_time"] == 0:
    release_time=[0] * len(job_id)
else:
    #the first week to  receive orders
    release_time = [random.randint(1,8) for i in range(len(job_id))]

if config["has_due_time"] == 0:
    due_time = [100000]*len(job_id)
else:
    # the last week to deliver orders
    due_time = [random.randint(24,31) for i in range(len(job_id))]

if config["has_weight"] == 0:
    weight = [0] * len(job_id)
else:
    weight = [random.randint(10, 50) for i in range(len(job_id))]

job_properties_df = pd.DataFrame(list(zip(job_id, release_time, due_time, weight)),
                                 columns=["job_id", "release_date", "due_date", "weight"])

# 任务在机器上的生产速度
job_machine = [[x, y] for x in job_id for y in machine_id]
job_machine_df = pd.DataFrame(job_machine, columns=["job_id", "machine_id"])
if config["machine_identical"] == 1:
    #the process time max 4 days
    speed = [random.randint(1, 5) for i in range(len(job_id))]
    speed_dict = dict(zip(job_id, speed))
    job_machine_df["speed"] = job_machine_df["job_id"].apply(lambda x: speed_dict[x])
else:
    speed = [random.randint(20, 51) for i in range(len(job_machine))]
    job_machine_df['speed'] = speed

# 任务间的前置关系
#mutiple succesors & multiple preccedors & overlap
overlap = [[0,3,1,2],[1,3,1,3],[1,4,2,3], [2,4,1,3], [3,5,1,2], [4,5,2,3],[6,7,4,4],[7,8,4,4],[9,10,2,2]]
precedence_df = pd.DataFrame(overlap,columns=["first_job_id", "second_job_id","delta_C_lower_bound","delta_C_upper_bound"])
#not overlap

# 工作顺序相关的换机调试时间
job_to_job = [[x,y,z] for x in range(len(job_id)) for y in range(len(job_id)) for z in range(len(machine_id))]
setup_df = pd.DataFrame(job_to_job, columns=["first_job_id", "second_job_id","machine_id"])
time=[]
if config["has_setup_time"] == 0:
    time=[0] * len(job_to_job)
else:
    time = [random.randint(1, 5) for i in range(len(job_to_job))]
setup_df["setup_time"] = time

writer = pd.ExcelWriter(r"..\input\parallel_template.xlsx")
job_properties_df.to_excel(writer,sheet_name="jobs", index=False)
job_machine_df.to_excel(writer,sheet_name="speeds", index=False)
precedence_df.to_excel(writer,sheet_name="precedence", index=False)
setup_df.to_excel(writer,sheet_name="setup", index=False)
writer.save()
writer.close()
