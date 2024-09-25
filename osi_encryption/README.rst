.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

========
Overview
========

This module simplifies the database encryption and sanitization process used for migration.

Features
========
* Users can choose which models and fields to encryption or sanitize
* Encryption is triggered via wizard where user enters the encruption key. It is NOT stored in the module.
* Sanitization is also triggered via wizard and requires a file location to store exported csv documents contianing the original data.
* Drop indexes in the event that encryption fails or not work correctly with indexes
* Encryption and Sanitization logs are available for each model that has the action run on it.

Configuration
=============

* Open the ''Encryption'' app that is visible from the main menu
* Generate Lines

  * Click on ''Generate Lines''' which will open a wizard with options to run when generating lines.

    * Line represent models and actions. Model Example: (res.partner (Contacts), Action Example: Encrypt)
    * Lines include which fields to include or exclude from the action. It also analyzises and shows indexes that can be dropped if needed.

    * Generate Lines Wizard Options:

      * Choose the Field Types to auto include in the included fields on the line.

        * Char - Standard field commonly encrypted or sanitized.
        * VarChar (Size Limit) - These are fields that have a set limit. The encryption handles these by resetting the size before encrypting the field in order to make sure the encrypted value can fit within the field. During Decryption, the size is reset back to the original setting.
        * Text - Standard field commonly encrypted or sanitized.

      * Common Exclusions: Enabling these will cause the lines for these particlar models to NOT be generated. These are included by default as it's expected each one be analyized and either included, excluded or adjusted according to the clients requirements.

        * Exclude ir_models = References any model with 'ir_' in it's name, mostly base models.
        * Exclude mail models = References any model with 'mail' in it's name.
        * Exclude report models = References any model with 'report' in it's name.

      * You can specify tables to exclude if desired. The lines once generated can also be excluded too if you want to generate lines for all models.
      * The query can be manually manipulated too, the Test query button will return the results of the query.
      * Clicking 'Generate Lines' will cause the system to auto genereate lines for all models queried. It will auto include fields that can be encrypted or sanitized and exclude the ones it cannot.

* Configure Lines

  * Lines will show:

    * Action:

      * Encryption
      * Sanitization

    * Model information: Name, Technical Name and link to model
    * Total # of Records: This is more of a snapshop with number of records when the line is created. It will only update if vacuum's and postgres cleanup operations are run where it would be recomputed. This is done for speed of counting.
    * Encryption/Decryption Times: Encrypting and Decrypting times are measured and will reflect in seconds how long it takes.
    * Exclude Ids: You can enter database ID's of records to exclude. This is useful for res.users for example to not encrypt the Admin account.
    * Included Char/Text Columns: Includes the field that will have the action run on.
    * Excluded Char/Text Columns: Includes fields that will be skipped by the action (like non-stored fields) or chosen to be skipped. We keep these on the line for reporting purposes.
    * Log: Shows a running log of the results of the action run.
    * Indexes: Lists indexes contained on the table of this model.
    * Status: Decrypted/Unsanitized/Encryped/Sanitized/Excluded/In Progress/Error

Usage
=====

* Encrypt/Decrypt

  * Start the encryption or decryption either by selecting multiple lines and go to Action menu and select either 'Encrypt or Sanitize'/'Decrypt or Desanitze' action, or clicking the correcsponding button when viewing an individual line.
  * Enter the encryption key. Keep the key in a safe place as it's needed for decrypting too and NOT kept anywhere in the database.

* Sanitize/Desanitize

  * Start the encryption or decryption either by selecting multiple lines and go to Action menu and select either 'Encrypt or Sanitize'/'Decrypt or Desanitze' action, or clicking the correcsponding button when viewing an individual line.
  * Enter the file location where the csv file will be stored or retreived. The CSV contains the original unsanitized data, outside of the database and is needed to restore the sanitized data.

* Notes:
  * You can run the actions for lines that have both actions, the wizard will ask both the key and CSV file location if there are lines that need it. Same for decrypting/unsanitzing. The system will run through each line sequentually.
  * Large tables can take time to run the action on (hours for very large table)
  * The actions do take into account status and exclusions. For example if the 'Encrypt' action is run on a line with status 'Encrypted' then it will skip it and not run on it again.

* Other usage items

  * Update # of Records

    * From the list or form view, go to Action - Updated # of Records to update the number of records for the selected models.
    * Note: This is a quick query that doesn't actually count records but instead looks in the database maintenance tables which are only periodically updated when maintenance tasks are performed (vacuums and such). This is used for speed, and give a close estimate.

  * Exclude/Include

    * From the list or form view, go to Action - Exclude Line(s) to exclude the selected models
    * From the list or form view, go to Action - Include Line(s) to include the selected models

  * Drop Index

    * In the Indexes tab on a line, click the ''Drop Index'' button.
    * Enter the name of the index to drop and click ''Drop Index''.
    * The dropped index will show in the ''Dropped Indexes'' field for future reference if needed.

Credits
=======

Contributors
------------

* OSI Dev Team <contact@opensourceintegrators.com>
* Patrick Wilson <pwilson@opensourceintegrators.com>
