from crewai.flow.flow import Flow, and_, listen, or_, start, router
from pydantic import BaseModel


class MyFirstFlowState(BaseModel):
    hello: str = ""


class MyFirstFlow(Flow[MyFirstFlowState]):
    @start()
    def start_flow(self):
        self.state.hello = "hello"
        print("hello start flow")
        return 123

    @listen(start_flow)
    def first_step(self, num):
        self.state.hello = "world"
        print("hello first step")
        print(f"num: {num}")

    @listen(first_step)
    def second_step(self):
        print(f"hello state: {self.state.hello}")

    @listen(or_(first_step, second_step))
    def and_dummy_func(self):
        print("and dummy func")

    @router(second_step)
    def router_to_end(self):
        print("router to end")

        check = True

        if check:
            return "check is True"
        else:
            return "check is False"

    @listen("check is True")
    def end_flow(self):
        print("end flow") 


flow = MyFirstFlow()
flow.kickoff()
