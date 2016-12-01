from dart_manager.util import DartManagerError



def update(self):
    if update_core: self._update_core()
    self._update_env()

def _update_env(self):
    pass

def _update_core(self):
    pass

def _update_stack(self, stack_config):
    stack_name = stack_config['Name']
    self.cf.create_change_set(
        ChangeSetName=self.generate_changeset_name(),
        StackName=stack_name,
        TemplateBody=self.get_template(stack_name),
    )