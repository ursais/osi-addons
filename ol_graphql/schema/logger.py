# Import Python Libs
import logging
from graphql import GraphQLError

_logger = logging.getLogger(__name__)


class GraphQLLogger:

    GQL_MUTATION_ERROR = "GQL_M_ERR"
    GQL_MUTATION_WARNING = "GQL_M_WRN"
    GRAFANA_ERROR_CODES = {
        GQL_MUTATION_ERROR: "Error in incoming GraphQL Mutation",
        GQL_MUTATION_WARNING: "Warning in incoming GraphQL Mutation",
    }

    def log_received_message(self, tid=False, message_source=False):
        """
        This function is intended to be overridden in later modules
        """
        data = ""
        if self.env["ir.config_parameter"].get_as_boolean(
            "ol_graphql.graphql_log_incoming_mutations", False
        ):
            data = f"| Data: {self.data}"
        _logger.info(
            f"GraphQL Mutation | S:1 | Received: {self.info.field_name} for `{self.odoo_class}` | UUID:"
            f" `{self.uuid}` {data} {self._get_message_source(message_source)} {self._get_tid(tid)}"
        )

    def log_info_message(self, msg, company=False, tid=False, message_source=False):
        """
        Dedicated function to ensure consistency in formatting
        """
        _logger.info(
            f"GraphQL | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)}"
        )

    def log_mutation_message(self, msg, company=False, tid=False, message_source=False):
        """
        Dedicated function to ensure consistency in formatting
        """

        _logger.info(
            f"GraphQL Mutation | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)}"
        )

    def log_warning_message(self, msg, company=False, tid=False, message_source=False):
        """
        Dedicated function to ensure consistency in formatting
        """
        _logger.warning(
            f"GraphQL Mutation Warning | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)} {self._get_grafana_error_code(self.GQL_MUTATION_WARNING)}"
        )

    def log_exception_message(
        self, msg, company=False, tid=False, message_source=False, traceback=True
    ):
        """
        Dedicated function to ensure consistency in formatting
        """
        _logger.exception(
            f"GraphQL Mutation Error | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)} {self._get_grafana_error_code(self.GQL_MUTATION_ERROR)}",
            exc_info=traceback,
        )

    def raise_ackable_exception(
        self, msg, company=False, tid=False, message_source=False, traceback=True
    ):
        """
        Dedicated function to ensure consistency in formatting.
        Note that these ackable exceptions are already formatted
        in our general GQL logic, so no need for those lines.
        """
        raise AckableException(
            f"GraphQL Mutation Ackable Exception | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)} {self._get_grafana_error_code(self.GQL_MUTATION_ERROR)}",
            traceback=traceback,
        )

    def raise_graphql_error(self, msg, company=False, tid=False, message_source=False):
        """
        Dedicated function to ensure consistency in formatting
        """
        raise GraphQLError(
            f"GraphQL Mutation Error | {msg} "
            f"{self._get_company(company)} {self._get_message_source(message_source)} {self._get_tid(tid)} {self._get_grafana_error_code(self.GQL_MUTATION_ERROR)}"
        )

    def _get_company(self, company):
        # company = company or self.env.company.short_name.upper()
        return f"| Company: {company}" if company else ""

    def _get_tid(self, tid):
        transaction_id = tid or (
            self.transaction_id if hasattr(self, "transaction_id") else False
        )
        return f"| TI: {transaction_id}" if transaction_id else ""

    def _get_grafana_error_code(self, code):
        return f"| GC: {code}"

    def _get_message_source(self, message_source):
        message_source = message_source or (
            self.message_source if hasattr(self, "message_source") else False
        )
        return f"| MS: {message_source}" if message_source else ""


class AckableException(Exception):
    """
    Class to handle situations when we don't want to continue processing the mutation
    but we can ACK the message so it's not getting retried at later time.
    """

    def __init__(self, message, traceback=True):
        self.message = message
        self.traceback = traceback
        super().__init__(self.message)

    def __str__(self):
        return self.message
