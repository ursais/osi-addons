from . import models


def post_init_hook_encrypt_decrypt(env):

    env['ir.actions.server'].decrypt_char_field()
    #env['ir.actions.server'].decrypt_number_field()
#    env['ir.actions.server'].decrypt_json_field()
